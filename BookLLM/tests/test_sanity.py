from BookLLM.src.quality import sanity


def test_find_unexpected_json():
    text = 'Intro {"a":1} end'
    assert sanity.find_unexpected_json(text) == ['{"a":1}']


def test_ignore_code_blocks():
    text = '```json\n{"a":1}\n```'
    assert sanity.find_unexpected_json(text) == []


def test_check_book_content():
    issues = sanity.check_book_content(["ok", '{"b":2}'])
    assert issues and "Section 2" in issues[0]
