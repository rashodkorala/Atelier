"""
Design archetype classifier.

Pipeline: TF-IDF vectoriser (unigrams + bigrams) → LogisticRegression.
Output: probability distribution across the six archetypes — not a hard label.
The distribution is passed to Claude as context, preserving uncertainty.

NumPy is used internally by scikit-learn for the feature matrix; pandas
manages the reference dataset via dataset.load_dataframe().
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder

from backend.classifier.dataset import ARCHETYPES, load_dataframe


class ArchetypeClassifier:
    """Wraps the scikit-learn pipeline and exposes a clean predict interface."""

    # Confidence below which we flag the output as low-confidence.
    LOW_CONFIDENCE_THRESHOLD = 0.40

    def __init__(self) -> None:
        self._pipeline: Pipeline | None = None
        self._label_encoder = LabelEncoder()
        self._label_encoder.fit(ARCHETYPES)

    def train(self) -> None:
        """Fit the pipeline on the labelled dataset."""
        df = load_dataframe()

        self._pipeline = Pipeline(
            [
                (
                    "tfidf",
                    TfidfVectorizer(
                        ngram_range=(1, 2),
                        sublinear_tf=True,
                        min_df=1,
                        max_features=5_000,
                        strip_accents="unicode",
                        analyzer="word",
                    ),
                ),
                (
                    "clf",
                    LogisticRegression(
                        C=2.0,
                        max_iter=1_000,
                        solver="lbfgs",
                        multi_class="multinomial",
                        random_state=42,
                    ),
                ),
            ]
        )

        self._pipeline.fit(df["brief"].tolist(), df["archetype"].tolist())

    def predict(self, brief: str) -> dict:
        """
        Classify a brief and return the full probability distribution.

        Returns
        -------
        {
            "primary": str,          # top archetype label
            "confidence": float,     # probability of the top class
            "distribution": dict,    # label → probability for all classes
            "low_confidence": bool,  # True when top prob < threshold
        }
        """
        if self._pipeline is None:
            raise RuntimeError("Classifier has not been trained. Call train() first.")

        brief_clean = brief.strip()
        if not brief_clean:
            raise ValueError("Brief cannot be empty.")

        # probas is shape (1, n_classes); classes are in pipeline order
        probas: np.ndarray = self._pipeline.predict_proba([brief_clean])[0]
        classes: list[str] = self._pipeline.classes_.tolist()

        # Build distribution dict sorted by probability descending
        distribution = {
            label: round(float(prob), 4)
            for label, prob in sorted(
                zip(classes, probas), key=lambda x: x[1], reverse=True
            )
        }

        top_label = max(distribution, key=distribution.__getitem__)
        top_prob = distribution[top_label]

        return {
            "primary": top_label,
            "confidence": round(top_prob, 4),
            "distribution": distribution,
            "low_confidence": top_prob < self.LOW_CONFIDENCE_THRESHOLD,
        }


# Module-level singleton — trained once at import time (FastAPI startup).
_classifier: ArchetypeClassifier | None = None


def get_classifier() -> ArchetypeClassifier:
    """Return the trained singleton classifier, training it on first call."""
    global _classifier
    if _classifier is None:
        _classifier = ArchetypeClassifier()
        _classifier.train()
    return _classifier
