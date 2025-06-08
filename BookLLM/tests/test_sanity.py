from BookLLM.src.quality.sanity import SanityChecker


def test_sanity_checker_detects_json():
    checker = SanityChecker()
    content = "Hello\n{\"foo\": \"bar\"}\nWorld"
    result = checker.check(content)
    assert not result["passed"]
    assert any("JSON snippet" in issue for issue in result["issues"])
