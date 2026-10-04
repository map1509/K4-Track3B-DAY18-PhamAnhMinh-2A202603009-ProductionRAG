"""Check dense indexing against real in-memory Qdrant without model downloads."""
import numpy as np
import pytest
from qdrant_client import QdrantClient
from config import EMBEDDING_DIM
from src.m2_search import DenseSearch, SearchResult, reciprocal_rank_fusion


class Encoder:
    def encode(self, texts, **kwargs):
        def vector(text):
            value = np.zeros(EMBEDDING_DIM)
            value[0 if 'leave' in text else 1] = 1
            return value
        return vector(texts) if isinstance(texts, str) else np.array([vector(t) for t in texts])


def test_dense_index_query_and_reindex():
    search = DenseSearch.__new__(DenseSearch)
    search.client = QdrantClient(':memory:')
    search._encoder = Encoder()
    try:
        search.index([{'text': 'leave policy', 'metadata': {'source': 'hr'}},
                      {'text': 'password policy', 'metadata': {'source': 'it'}}], 'test')
        results = search.search('leave', top_k=1, collection='test')
        assert results[0].text == 'leave policy'
        assert results[0].method == 'dense'
        assert results[0].metadata == {'source': 'hr'}
        assert results[0].score == pytest.approx(1.0)
        search.index([], 'test')
        assert search.search('leave', collection='test') == []
    finally:
        search.client.close()


def test_rrf_uses_rank_and_preserves_inputs():
    a = SearchResult('a', 500, {'source': 'a'}, 'bm25')
    b = SearchResult('b', 0.1, {}, 'dense')
    merged = reciprocal_rank_fusion([[a, b], [b]])
    assert merged[0].text == 'b'
    assert merged[0].score == pytest.approx(1 / 62 + 1 / 61)
    assert merged[0].method == 'hybrid'
    assert a.score == 500
    assert reciprocal_rank_fusion([[a]], top_k=0) == []
