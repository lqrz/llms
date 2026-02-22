"""Evaluator."""

from llama_index.core.evaluation import (
    FaithfulnessEvaluator,
    RelevancyEvaluator,
    CorrectnessEvaluator,
)
from llama_index.core.evaluation import BatchEvalRunner
import asyncio
from typing import Callable, Dict, List
from collections import defaultdict
from glob import glob
from pathlib import Path
import pandas as pd

from llms.agent.evaluation.evaluation_sample import EvaluationSample


class Evaluator:

    def __init__(self, llm_model, path_input_data: str):
        """Init."""
        self._evaluator_faithfulness = FaithfulnessEvaluator(llm=llm_model)
        self._evaluator_relevancy = RelevancyEvaluator(llm=llm_model)
        self._evaluator_correctness = CorrectnessEvaluator(llm=llm_model)
        self._company_files = self._get_company_files_from_data(
            path_input=path_input_data
        )

    @staticmethod
    def _get_company_files_from_data(path_input: str) -> Dict[str, List]:
        """Get company files from data."""
        company_files: Dict[str, List] = defaultdict(list)
        for x in glob(f"{path_input}/*.pdf"):
            p = Path(x)
            company: str = p.stem.split(" ")[-1]
            company_files[company].append(p.name.strip(".pdf"))
        return company_files

    def _get_dataset_from_df(
        self,
        df: pd.DataFrame,
    ) -> List[EvaluationSample]:
        """Get dataset from Pandas df."""
        rows = df.to_dict("records")
        dataset: List[EvaluationSample] = [
            EvaluationSample.from_row(r, self.company_files) for r in rows
        ]
        return dataset

    async def evaluate_sample(
        self,
        sample: EvaluationSample,
        f_graph_invoke: Callable,
    ):
        """Evaluate dataset sample."""
        query: str = sample.query
        answer: str = sample.answer
        source_docs: List[str] = sample.source_docs
        question_type: str = sample.question_type

        # invoke graph
        reponse = f_graph_invoke(query)

        # evaluate rag triad
        result_relevancy = await self._evaluator_relevancy.aevaluate(
            query=query,
            contexts=contexts,
        ).score

        result_faithfulness = await self._evaluator_faithfulness.aevaluate(
            query=query,
            response=reponse["answer"],
            contexts=contexts,
        )

        result_correctness = await self._evaluator_correctness.aevaluate(
            query=query,
            response=reponse["answer"],
            reference=answer,
        )

        # return
        result = {
            "query": sample,
            "relevancy": result_relevancy.score,  # 0..1 :contentReference[oaicite:5]{index=5}
            "faithfulness": result_faithfulness.score,  # typically boolean/score depending on evaluator :contentReference[oaicite:6]{index=6}
            "correctness": result_correctness.score,  # 1..5 :contentReference[oaicite:8]{index=8}
            # "retrieval_hit@k": hit,
            # "retrieval_recall@k": recall,
            "feedback": {
                "relevancy": result_relevancy.feedback,
                "faithfulness": result_faithfulness.feedback,
                "correctness": result_correctness.feedback,
            },
        }

        return result

    async def evaluate_dataset(
        self,
        df: pd.DataFrame,
        f_graph_invoke: Callable,
        concurrency: int = 20,
    ):
        """Evaluate dataset sample."""
        semaphore = asyncio.Semaphore(concurrency)

        async def wrapped(sample: EvaluationSample):
            async with semaphore:
                return await self.evaluate_sample(sample, f_graph_invoke)

        dataset: List[EvaluationSample] = self._get_dataset_from_df(df=df)
        return await asyncio.gather(*[wrapped(sample) for sample in dataset])
