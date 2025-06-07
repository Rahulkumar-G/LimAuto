import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


class TokenMetricsTracker:
    """Track and analyze token usage and costs."""

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset all metrics"""
        self.metrics = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "requests": 0,
            "total_cost": 0.0,
            "start_time": datetime.now().isoformat(),
            "history": [],
        }
        self._seen_requests = set()

    def add_usage(
        self,
        input_tokens: int,
        output_tokens: int,
        cost_config: Any = None,
        request_id: str | None = None,
    ) -> None:
        """Record token usage and cost.

        Parameters
        ----------
        input_tokens: int
            Number of prompt tokens sent to the model.
        output_tokens: int
            Number of tokens returned by the model.
        cost_config: Any, optional
            Object with cost configuration (``cost_per_input_token``,
            ``cost_per_output_token`` and ``cost_per_request`` attributes).
        """
        if request_id and request_id in self._seen_requests:
            return

        cost = 0.0
        if cost_config is not None:
            try:
                cost = (
                    input_tokens * getattr(cost_config, "cost_per_input_token", 0.0)
                    + output_tokens * getattr(cost_config, "cost_per_output_token", 0.0)
                    + getattr(cost_config, "cost_per_request", 0.0)
                )
            except Exception:
                cost = 0.0

        usage = {
            "timestamp": datetime.now().isoformat(),
            "request_id": self.metrics["requests"] + 1,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost": cost,
        }

        # Update totals
        self.metrics["input_tokens"] += input_tokens
        self.metrics["output_tokens"] += output_tokens
        self.metrics["total_tokens"] += input_tokens + output_tokens
        self.metrics["total_cost"] += usage["cost"]
        self.metrics["requests"] += 1

        # Add to history
        self.metrics["history"].append(usage)

        if request_id:
            self._seen_requests.add(request_id)

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of token usage and costs"""
        return {
            "total_tokens": self.metrics["total_tokens"],
            "input_tokens": self.metrics["input_tokens"],
            "output_tokens": self.metrics["output_tokens"],
            "requests": self.metrics["requests"],
            "total_cost_usd": round(self.metrics["total_cost"], 4),
            "avg_tokens_per_request": round(
                (
                    self.metrics["total_tokens"] / self.metrics["requests"]
                    if self.metrics["requests"] > 0
                    else 0
                ),
                2,
            ),
            "start_time": self.metrics["start_time"],
            "end_time": datetime.now().isoformat(),
        }

    def save_metrics(self, path: Path) -> None:
        """Save metrics to JSON file"""
        with open(path, "w") as f:
            json.dump(self.metrics, f, indent=2)


class QualityMetricsTracker:
    """Track and analyze content quality metrics"""

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset all quality metrics"""
        self.metrics = {
            "readability_scores": {},
            "technical_accuracy": {},
            "consistency_scores": {},
            "content_coverage": {},
            "start_time": datetime.now().isoformat(),
            "history": [],
        }

    def add_quality_score(
        self,
        metric_type: str,
        chapter: str,
        score: float,
        details: Dict[str, Any] = None,
    ) -> None:
        """Record quality metric"""
        if metric_type not in self.metrics:
            self.metrics[metric_type] = {}

        self.metrics[metric_type][chapter] = {
            "score": score,
            "timestamp": datetime.now().isoformat(),
            "details": details or {},
        }

    def get_quality_summary(self) -> Dict[str, Any]:
        """Get summary of quality metrics"""
        summary = {
            "overall_scores": {},
            "per_chapter_scores": {},
            "start_time": self.metrics["start_time"],
            "end_time": datetime.now().isoformat(),
        }

        # Calculate averages for each metric type
        for metric_type, scores in self.metrics.items():
            if isinstance(scores, dict):
                chapter_scores = [s["score"] for s in scores.values()]
                if chapter_scores:
                    summary["overall_scores"][metric_type] = sum(chapter_scores) / len(
                        chapter_scores
                    )
                    summary["per_chapter_scores"][metric_type] = scores

        return summary

    def save_metrics(self, path: Path) -> None:
        """Save quality metrics to JSON file"""
        with open(path, "w") as f:
            json.dump(self.metrics, f, indent=2)
