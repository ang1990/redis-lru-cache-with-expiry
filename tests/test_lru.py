import fakeredis
from unittest import TestCase
from lru_cache import LRUCache


class TestLRU(TestCase):
    def setUp(self) -> None:
        self.redis = fakeredis.FakeStrictRedis(decode_responses=True)

    def test_create_lru(self) -> None:
        LRUCache(self.redis, limit=0, cache_key='test-lru')