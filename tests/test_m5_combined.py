"""Test combined enrichment with mocked API responses."""
import json
import sys
from types import SimpleNamespace
import pytest
import src.m5_enrichment as enrichment


def fake_api(monkeypatch, content):
    calls = []
    def create(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])
    monkeypatch.setattr(enrichment, 'OPENAI_API_KEY', 'test-key')
    monkeypatch.setitem(sys.modules, 'openai', SimpleNamespace(
        OpenAI=lambda **kwargs: SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))))
    return calls


def test_one_call_and_indexed_enrichment(monkeypatch):
    calls = fake_api(monkeypatch, json.dumps({'summary': 'Summary', 'questions': ['Question?'],
        'context': 'Context', 'metadata': {'source': 'invented', 'parent_id': 'wrong', 'topic': 'hr'}}))
    chunks = [{'text': 'Original', 'metadata': {'source': 'hr.md', 'parent_id': 'parent_0'}}]
    result = enrichment.enrich_chunks(chunks)[0]
    assert len(calls) == 1
    assert calls[0]['model'] == 'gpt-4o-mini'
    assert 'Phân tích đoạn văn' in calls[0]['messages'][0]['content']
    assert calls[0]['response_format'] == {'type': 'json_object'}
    assert result.enriched_text.startswith('Context\n\nOriginal')
    assert 'Question?' in result.enriched_text and 'Summary' in result.enriched_text
    assert result.auto_metadata['source'] == 'hr.md'
    assert result.auto_metadata['parent_id'] == 'parent_0'
    assert chunks[0]['text'] == 'Original'


@pytest.mark.parametrize('content', ['invalid JSON', '{"summary": 1}', '[]'])
def test_invalid_response_falls_back(monkeypatch, content):
    calls = fake_api(monkeypatch, content)
    result = enrichment._enrich_single_call('First sentence. Second sentence.', 'hr.md')
    assert len(calls) == 1
    assert result['summary'] == 'First sentence. Second sentence.'
    assert 'hr.md' in result['context']
    assert result['questions']


def test_no_key_does_not_call_api(monkeypatch):
    calls = fake_api(monkeypatch, '{}')
    monkeypatch.setattr(enrichment, 'OPENAI_API_KEY', '')
    assert enrichment.generate_hypothesis_questions('Policy applies.', 0) == []
    result = enrichment._enrich_single_call('Policy applies.', 'policy.md')
    assert result['summary'] == 'Policy applies.'
    assert calls == []
