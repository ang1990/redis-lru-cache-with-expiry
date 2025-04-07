# Redis LRU Cache

### Installation
``` pip install redis-lru```

### Introduction
This is an implementation of an LRU cache powered by Redis.

Usage:

```python

from redis import StrictRedis
from lru_cache import LRUCache

# bring your own redis connection

strict_redis = StrictRedis(...)
lru_cache = LRUCache(strict_redis, limit=99, cache_key='test-cache', timeout=3600)

lru_cache.set('test1', 'testvalue')

lru_cache.get('test1')
# 'testvalue'

lru_cache.delete('test1')
# 1

lru_cache.get('test1')
# None

```