from BookLLM.src.agents.review.readability_tuner import ReadabilityTuner
from BookLLM.src.utils.case_study_formatter import CaseStudyFormatter


def test_readability_tuner():
    text = (
        "This sentence is deliberately verbose and complex so that it will exceed"
        " the typical length expected from concise communication, thereby raising"
        " the Flesch Kincaid grade level considerably beyond twelve."
    )
    tuner = ReadabilityTuner()
    result = tuner.tune(text)
    assert result.grade >= 0
    assert result.suggestions


def test_case_study_formatter():
    formatted = CaseStudyFormatter.format("Example case study")
    assert formatted.startswith("> **Case Study**")
    assert "> Example case study" in formatted
