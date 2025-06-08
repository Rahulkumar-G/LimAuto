from BookLLM.src.utils.style_guide import StyleGuideEnforcer


def test_style_enforcer_basic():
    raw = "#Title\n####Heading\nText\n*italic* and __bold__\n"
    expected = "# Title\n\n## Heading\n\nText\n_italic_ and **bold**\n"
    assert StyleGuideEnforcer.enforce(raw) == expected
