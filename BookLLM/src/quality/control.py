from datetime import datetime
from typing import Any, Dict, List

from ..agents.review import ContentValidator, ProofreaderAgent
from ..models.state import BookState
from ..utils.logger import get_logger
from .metrics import QualityMetrics
from . import sanity


class QualityControl:
    """Orchestrates comprehensive quality control processes for book content"""

    def __init__(self, llm):
        self.llm = llm
        self.logger = get_logger(__name__)
        self.validator = ContentValidator()
        self.proofreader = ProofreaderAgent(llm)
        self.metrics = QualityMetrics()

        # Quality thresholds
        self.quality_thresholds = {
            "readability": 0.7,
            "consistency": 0.8,
            "technical_accuracy": 0.9,
            "overall": 0.8,
        }

    async def run_quality_checks(self, state: BookState) -> BookState:
        """Execute comprehensive quality control pipeline"""
        try:
            self.logger.info("Starting quality control process")

            # Step 1: Content Validation
            validation_results = await self.validator.validate(state)
            state.metadata["validation_results"] = validation_results

            # Step 2: Proofreading
            state = self.proofreader.process(state)

            # Step 3: Quality Metrics
            quality_scores = self.metrics.calculate_scores(state, validation_results)
            state.metadata["quality_scores"] = quality_scores

            # Step 4: Technical Review
            await self._perform_technical_review(state)

            # Step 5: Readability Analysis
            await self._analyze_readability(state)

            # Step 5.5: Sanity check for JSON artifacts
            sanity_issues = sanity.check_book_content(list(state.chapter_map.values()))
            if sanity_issues:
                state.warnings.extend(sanity_issues)
                state.metadata["sanity_issues"] = sanity_issues

            # Step 6: Generate Quality Report
            state.metadata["quality_report"] = await self._generate_detailed_report(
                state, validation_results, quality_scores
            )

            # Step 7: Improvement Recommendations
            if not self._meets_quality_standards(quality_scores):
                state.metadata["improvement_plan"] = (
                    await self._generate_improvement_plan(state)
                )

            self.logger.info("Quality control process completed")
            return state

        except Exception as e:
            self.logger.error(f"Quality control failed: {str(e)}")
            state.errors.append(f"Quality control error: {str(e)}")
            return state

    async def _perform_technical_review(self, state: BookState) -> None:
        """Perform technical content review"""
        for chapter_title, content in state.chapter_map.items():
            prompt = f"""
            Perform technical review for chapter: {chapter_title}
            
            Check for:
            1. Technical accuracy
            2. Code correctness (if present)
            3. Current best practices
            4. Factual correctness
            5. Technical terminology usage
            
            Content: {content[:2000]}...
            """

            try:
                review_result, _ = await self.llm.acall_llm(prompt)
                if not state.metadata.get("technical_reviews"):
                    state.metadata["technical_reviews"] = {}
                state.metadata["technical_reviews"][chapter_title] = review_result
            except Exception as e:
                self.logger.warning(f"Technical review failed for {chapter_title}: {e}")

    async def _analyze_readability(self, state: BookState) -> None:
        """Analyze content readability"""
        from textstat import textstat

        readability_scores = {}
        for chapter_title, content in state.chapter_map.items():
            scores = {
                "flesch_reading_ease": textstat.flesch_reading_ease(content),
                "flesch_kincaid_grade": textstat.flesch_kincaid_grade(content),
                "gunning_fog": textstat.gunning_fog(content),
                "smog_index": textstat.smog_index(content),
            }
            readability_scores[chapter_title] = scores

        state.metadata["readability_analysis"] = readability_scores

    async def _generate_detailed_report(
        self,
        state: BookState,
        validation_results: List[Dict],
        quality_scores: Dict[str, float],
    ) -> Dict[str, Any]:
        """Generate comprehensive quality report"""
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_score": sum(quality_scores.values()) / len(quality_scores),
            "validation_summary": self._summarize_validation(validation_results),
            "quality_metrics": quality_scores,
            "readability_summary": self._summarize_readability(state),
            "technical_accuracy": self._summarize_technical_review(state),
            "recommendations": self._compile_recommendations(validation_results),
            "improvement_areas": self._identify_improvement_areas(quality_scores),
            "quality_standards_met": self._meets_quality_standards(quality_scores),
        }

    def _meets_quality_standards(self, quality_scores: Dict[str, float]) -> bool:
        """Check if content meets quality standards"""
        return all(
            score >= self.quality_thresholds.get(metric, 0.7)
            for metric, score in quality_scores.items()
        )

    async def _generate_improvement_plan(self, state: BookState) -> Dict[str, Any]:
        """Generate specific improvement recommendations"""
        low_quality_areas = [
            metric
            for metric, score in state.metadata["quality_scores"].items()
            if score < self.quality_thresholds.get(metric, 0.7)
        ]

        improvement_plan = {
            "priority_areas": low_quality_areas,
            "specific_actions": [],
            "estimated_effort": {},
        }

        for area in low_quality_areas:
            prompt = f"""
            Generate specific improvement actions for: {area}
            Current score: {state.metadata['quality_scores'][area]}
            Target score: {self.quality_thresholds.get(area, 0.7)}
            
            Provide:
            1. Specific actions to improve
            2. Estimated effort (in hours)
            3. Expected impact
            """

            try:
                response, _ = await self.llm.acall_llm(prompt)
                improvement_plan["specific_actions"].append(
                    {"area": area, "recommendations": response}
                )
            except Exception as e:
                self.logger.warning(
                    f"Failed to generate improvement plan for {area}: {e}"
                )

        return improvement_plan

    def _summarize_validation(self, validation_results: List[Dict]) -> Dict[str, Any]:
        """Summarize validation results"""
        return {
            "total_checks": len(validation_results),
            "passed_checks": sum(1 for r in validation_results if r["passed"]),
            "failed_checks": sum(1 for r in validation_results if not r["passed"]),
            "critical_issues": [
                r
                for r in validation_results
                if not r["passed"] and r.get("severity") == "critical"
            ],
        }

    def _summarize_readability(self, state: BookState) -> Dict[str, Any]:
        """Summarize readability analysis"""
        readability = state.metadata.get("readability_analysis", {})
        if not readability:
            return {}

        return {
            "average_scores": {
                metric: sum(ch[metric] for ch in readability.values())
                / len(readability)
                for metric in next(iter(readability.values())).keys()
            },
            "problematic_chapters": [
                chapter
                for chapter, scores in readability.items()
                if scores["flesch_reading_ease"] < 50
            ],
        }
