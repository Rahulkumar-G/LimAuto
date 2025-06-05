from typing import Dict, List

from ..models.state import BookState


class QualityMetrics:
    """Handles quality metrics calculation and analysis"""

    def calculate_scores(
        self, state: BookState, validation_results: List[Dict]
    ) -> Dict[str, float]:
        """Calculate quality scores from validation results"""
        scores = {
            "readability": self._calculate_readability_score(state),
            "consistency": self._calculate_consistency_score(validation_results),
            "completeness": self._calculate_completeness_score(state),
            "technical_accuracy": self._calculate_technical_score(validation_results),
        }

        # Add weight-based overall score
        weights = {
            "readability": 0.3,
            "consistency": 0.3,
            "completeness": 0.2,
            "technical_accuracy": 0.2,
        }

        scores["overall"] = sum(
            score * weights[metric]
            for metric, score in scores.items()
            if metric in weights
        )

        return scores
