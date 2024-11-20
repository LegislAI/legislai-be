import os

import dspy
from dotenv import load_dotenv
from langchain_together import Together

load_dotenv()
llm = Together(
    model="mistralai/Mistral-7B-Instruct-v0.1",
    together_api_key=os.getenv("TOGETHER_API_KEY"),
    max_tokens=1000,
)
