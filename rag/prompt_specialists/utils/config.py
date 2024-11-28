import os

import dspy
from dotenv import load_dotenv

load_dotenv()


class Config:
    def __init__(self):
        self.together_api_key = os.getenv("TOGETHER_API_KEY")
        self.main_model = "together_ai/meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"
        self.max_tokens = 8000

    def setup_models(self):
        lm = dspy.LM(
            self.main_model,
            api_key=self.together_api_key,
            cache=False,
            max_tokens=self.max_tokens,
        )
        dspy.configure(lm=lm)
        return lm
