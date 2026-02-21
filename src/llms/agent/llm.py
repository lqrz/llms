"""LLM."""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

_ = load_dotenv()


OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
LLM_MODEL = "gpt-4o-mini"
TEMPERATURE = 0.1


LLM = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model=LLM_MODEL,
    temperature=TEMPERATURE,
)
