import os

import dspy
from dotenv import load_dotenv

load_dotenv()


class Config:
    def __init__(self):
        self.together_api_key = os.getenv("TOGETHER_API_KEY")
        self.main_model = "together_ai/meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"
        self.metric_model = "together_ai/google/gemma-2-9b-it"
        self.max_tokens = 1500

    def setup_models(self):
        lm = dspy.LM(
            self.main_model,
            api_key=self.together_api_key,
            cache=False,
            max_tokens=self.max_tokens,
        )
        dspy.configure(lm=lm)
        metric_lm = dspy.LM(
            self.metric_model, cache=False, api_key=self.together_api_key
        )
        return lm, metric_lm
