from BookLLM.src.agents.review.readability_consistency import (
    ReadabilityConsistencyChecker,
)


def test_readability_consistency_checker():
    checker = ReadabilityConsistencyChecker({"AI": "artificial intelligence"})
    text = (
        "Artificial intelligence (AI) is widely used. "
        "The dataset was processed by the algorithm. "
        "This methodology synergistically leverages resources."
    )
    report = checker.analyze(text)
    assert report.readability["flesch_kincaid_grade"] >= 0
    assert any("processed by" in s for s in report.passive_sentences)
    assert "synergistically" in report.jargon
    assert report.terminology_issues
