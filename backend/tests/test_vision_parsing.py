"""Tests du parsing défensif des réponses vision.

Le prompt système exige du JSON pur, mais les LLMs ajoutent parfois des fences
markdown ou un préambule. _strip_json doit tolérer ces cas.
"""
import json
from app.grading.vision import _strip_json


def test_strip_pure_json():
    src = '{"items": [{"q": "1"}]}'
    assert json.loads(_strip_json(src)) == {"items": [{"q": "1"}]}


def test_strip_markdown_fence():
    src = '```json\n{"items": []}\n```'
    assert json.loads(_strip_json(src)) == {"items": []}


def test_strip_fence_no_lang():
    src = '```\n{"a": 1}\n```'
    assert json.loads(_strip_json(src)) == {"a": 1}


def test_strip_prose_around():
    src = 'Voici le JSON demandé :\n{"items": []}\nFin.'
    assert json.loads(_strip_json(src)) == {"items": []}


def test_strip_trailing_text():
    src = '{"items": [{"x": 2}]}\nAvec des notes.'
    assert json.loads(_strip_json(src)) == {"items": [{"x": 2}]}
