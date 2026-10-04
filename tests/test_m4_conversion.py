"""Verify score conversion and diagnostic selection without external APIs."""
import sys
from types import SimpleNamespace
import pandas as pd
import pytest
from src.m4_eval import evaluate_ragas, failure_analysis, EvalResult

NAMES = ['faithfulness', 'answer_relevancy', 'context_precision', 'context_recall']


def install_fakes(monkeypatch, rows):
    metrics = [object() for _ in NAMES]
    monkeypatch.setitem(sys.modules, 'ragas.metrics', SimpleNamespace(**dict(zip(NAMES, metrics))))
    def evaluate(dataset, **kwargs):
        assert kwargs['metrics'] == metrics
        assert dataset['question'] == ['q1', 'q2']
        return SimpleNamespace(to_pandas=lambda: pd.DataFrame(rows))
    monkeypatch.setitem(sys.modules, 'ragas', SimpleNamespace(evaluate=evaluate))
    monkeypatch.setitem(sys.modules, 'datasets', SimpleNamespace(
        Dataset=SimpleNamespace(from_dict=lambda data: data)))


def test_evaluation_converts_rows_and_averages(monkeypatch):
    install_fakes(monkeypatch, [dict.fromkeys(NAMES, 0.2), dict.fromkeys(NAMES, 0.8)])
    result = evaluate_ragas(['q1', 'q2'], ['a1', 'a2'], [['c1'], ['c2']], ['g1', 'g2'])
    assert all(result[name] == pytest.approx(0.5) for name in NAMES)
    assert result['per_question'][1].question == 'q2'
    assert result['per_question'][1].contexts == ['c2']
    assert result['per_question'][1].faithfulness == 0.8


def test_nonfinite_scores_trigger_fallback(monkeypatch, capsys):
    install_fakes(monkeypatch, [dict.fromkeys(NAMES, float('nan')), dict.fromkeys(NAMES, 0.8)])
    result = evaluate_ragas(['q1', 'q2'], ['a1', 'a2'], [['c1'], ['c2']], ['g1', 'g2'])
    assert result['per_question'] == []
    assert result['status'] == 'failed'
    assert 'ValueError' in capsys.readouterr().out


def test_failure_analysis_selects_lowest_average_and_metric():
    good = EvalResult('good', '', [], '', 0.9, 0.9, 0.9, 0.9)
    bad = EvalResult('bad', '', [], '', 0.5, 0.6, 0.4, 0.1)
    result = failure_analysis([good, bad], bottom_n=1)
    assert result[0]['question'] == 'bad'
    assert result[0]['worst_metric'] == 'context_recall'
    assert result[0]['score'] == pytest.approx(0.4)
    assert 'BM25' in result[0]['suggested_fix']
    assert failure_analysis([bad], bottom_n=0) == []
