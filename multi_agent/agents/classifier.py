from datetime import datetime
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import numpy as np
import spacy
from lime.lime_text import LimeTextExplainer


class CodeClassificationAgent:
    def __init__(
        self,
        model_path: str = "/home/francisca/Desktop/mei/LEGISLAI/legislai-be/multi_agent/classifier_nlp/model-best",
    ):
        """
        Initialize the code classification agent.
        """
        self.nlp = spacy.load(model_path)

    def run(self, query: str) -> Dict[str, Any]:
        """
        Run the code classification agent on a given query.
        """
        try:
            classifications = self._classify_text(query)

            # Get LIME explanation
            # explanation = self._get_explanation(query)

            response = {"classifications": classifications}

            return response

        except Exception as e:
            print(f"Error during classification: {e}")
            return self._get_default_response(query)

    def _classify_text(self, text: str) -> List[Dict[str, float]]:
        """
        Classify the input text using the spaCy model.
        """
        doc = self.nlp(self._remove_stopwords(text))
        sorted_cats = sorted(doc.cats.items(), key=lambda x: x[1], reverse=True)

        return [{"category": cat, "score": float(score)} for cat, score in sorted_cats]

    def _get_explanation(self, text: str) -> Dict[str, Any]:
        """
        Get LIME explanation for the classification.
        """
        doc = self.nlp(self._remove_stopwords(text))
        sorted_cats = sorted(doc.cats.items(), key=lambda x: x[1], reverse=True)

        def predict_proba(texts):
            docs = [self.nlp(text) for text in texts]
            return np.array(
                [[doc.cats.get(cat, 0.0) for cat, _ in sorted_cats] for doc in docs]
            )

        explainer = LimeTextExplainer(class_names=[cat for cat, _ in sorted_cats])

        exp = explainer.explain_instance(
            self._remove_stopwords(text), predict_proba, num_features=10, num_samples=3
        )

        # Convert explanation to serializable format
        explanation = {
            "feature_weights": [
                {"feature": feature, "weight": weight}
                for feature, weight in exp.as_list()
            ],
            "class_names": exp.class_names,
            "top_labels": exp.top_labels,
        }

        return explanation

    def _remove_stopwords(self, text: str) -> str:
        """
        Remove stopwords from input text.
        """
        doc = self.nlp(text)
        filtered_words = [
            token.text for token in doc if not token.is_stop and not token.is_punct
        ]  # Filtra stop words e pontuação
        return " ".join(filtered_words)

    def _get_default_response(self, query: str) -> Dict[str, Any]:
        """
        Return default response when classification fails.

        """
        return {"classifications": []}


def code_classification_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agent function that can be used in the state graph.
    """
    agent = CodeClassificationAgent()
    classification_result = agent.run(state["query"])

    # Update the state with the classification results
    state["code"] = [classification_result]
    return state
