import pytest
from BookLLM.src.utils.pre_filters import remove_outline_dicts


def test_remove_outline_dicts():
    text = "Chapter 1: [{\"title\": \"Intro\"}]\nSome content\nChapter 2: [{\"title\": \"Next\"}]\n"
    expected = "Some content\n"
    assert remove_outline_dicts(text) == expected

