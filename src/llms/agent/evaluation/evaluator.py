"""Evaluator."""

from llama_index.core.evaluation import (
    FaithfulnessEvaluator,
    RelevancyEvaluator,
    CorrectnessEvaluator,
    EvaluationResult,
)
from llama_index.core.evaluation import BatchEvalRunner
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import StateSnapshot
import asyncio
from typing import Callable, Dict, List, Any
from collections import defaultdict
from glob import glob
from pathlib import Path
import pandas as pd

from llms.agent.evaluation.evaluation_sample import EvaluationSample
from llms.agent.graph.utils import graph_invoke
from llms.agent.graph.state import BasicState


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
            EvaluationSample.from_row(r, self._company_files) for r in rows
        ]
        return dataset

    @staticmethod
    async def _f_graph_invoke(graph, query, id) -> Dict[str, Any]:
        """Graph invoke."""
        _, result, _, _ = await graph_invoke(
            message=query, thread_id=id, graph=graph, metadata={}
        )
        return result

    async def evaluate_sample(
        self,
        graph: CompiledStateGraph,
        sample: EvaluationSample,
    ):
        """Evaluate dataset sample."""
        id: int = sample.id
        query: str = sample.query
        answer: str = sample.answer
        # source_docs: List[str] = sample.source_docs
        # query_type: str = sample.query_type

        # invoke graph
        response: Dict[str, Any] = await self._f_graph_invoke(
            graph=graph, query=query, id=id
        )

        # evaluate rag triad
        result_correctness: EvaluationResult = (
            await self._evaluator_correctness.aevaluate(
                query=query,
                response=response["answer"],
                reference=answer,
            )
        )

        result_relevancy = EvaluationResult(score=None, feedback=None)
        result_faithfulness = EvaluationResult(score=None, feedback=None)

        if "rag_contexts" in response:
            result_relevancy: EvaluationResult = (
                await self._evaluator_relevancy.aevaluate(
                    query=query,
                    contexts=response.get("rag_contexts", None),
                )
            )

            result_faithfulness: EvaluationResult = (
                await self._evaluator_faithfulness.aevaluate(
                    query=query,
                    response=response["answer"],
                    contexts=response.get("rag_contexts", None),
                )
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
        graph: CompiledStateGraph,
        concurrency: int = 20,
    ):
        """Evaluate dataset sample."""
        semaphore = asyncio.Semaphore(concurrency)

        async def wrapped(sample: EvaluationSample):
            async with semaphore:
                return await self.evaluate_sample(graph=graph, sample=sample)

        dataset: List[EvaluationSample] = self._get_dataset_from_df(df=df)
        return await asyncio.gather(*[wrapped(sample) for sample in dataset])


if __name__ == "__main__":

    from llama_index.llms.openai import OpenAI
    from llms.agent.graph.graph_builds import build_basic_graph

    llm_model_name: str = "gpt-4.1-mini"
    path_input_data: str = "data/sec_filings"
    llm_model = OpenAI(model=llm_model_name)
    evaluator = Evaluator(llm_model=llm_model, path_input_data=path_input_data)
    path_input_dataset: str = "data/evaluation/qna_data_mini.csv"
    df = pd.read_csv(open(path_input_dataset))
    dataset = evaluator._get_dataset_from_df(df=df)
    sample = dataset[0]
    graph = build_basic_graph()
    result = asyncio.run(evaluator.evaluate_sample(graph=graph, sample=sample))
    result
