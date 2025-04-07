from redis import StrictRedis
import time


class LRUCache:
    _redis_conn: StrictRedis
    cache_key: str = ''
    limit: int = -1  # 0 means no limit, negative is invalid init
    timeout: int = 0   # cache timeout in seconds, 0 means no timeout
    _last_used_cache_name: str = ''
    _last_used_expiry_cache_name: str = ''

    def __init__(self, redis_conn: StrictRedis, limit: int, cache_key: str, timeout: int = 0, *, last_used_cache_name: str = '') -> None:
        assert redis_conn is not None
        self._redis_conn = redis_conn
        self._redis_conn.connection.encoder.decode_responses = True  # So we can get primitive types automatically
        assert cache_key
        self.cache_key = cache_key

        self.timeout = max(timeout, 0)

        self._last_used_cache_name = last_used_cache_name or f'{cache_key}_queue'
        self._last_used_expiry_cache_name = f'{cache_key}_expiry'

        self.limit = limit
        assert self.limit > -1

    def _trim_lru_to_limit(self) -> None:
        if self.limit <= 0:
            return

        # try to remove timed-out keys first
        count_to_remove = self._redis_conn.zcard(self._last_used_cache_name) - self.limit
        if count_to_remove > 0:
            if removed := self._remove_expired_keys():
                count_to_remove -= removed

        if count_to_remove > 0:
            oldest_keys = self._redis_conn.zrange(self._last_used_cache_name, 0, -1, num=count_to_remove)
            assert all(k.startswith(self.cache_key) for k in oldest_keys)
            self.delete(*oldest_keys)

    def _to_redis_key(self, key: str) -> str:
        return f'{self.cache_key}:{key}'

    def _touch_key(self, key: str) -> None:
        touch_time = int(time.time())
        self._redis_conn.zadd(self._last_used_cache_name, {key: touch_time})

    @property
    def _implements_timeout(self) -> bool:
        return self.timeout != 0

    def _remove_expired_keys(self) -> int:
        if not self._implements_timeout:
            return 0

        timed_out_keys: list[str] = self._redis_conn.zrange(
            self._last_used_expiry_cache_name,
            0,
            int(time.time())
        )

        if timed_out_keys:
            self.delete(*timed_out_keys)
        return len(timed_out_keys)

    def get(self, key: str) -> str | int | bool | None:
        value = self.peek(key)  # what if value stored in redis is null?
        if value is not None:
            self._touch_key(key)
        return value

    def set(self, key: str, value: str | int | bool) -> None:
        kwargs = {'ex': self.timeout} if self._implements_timeout else {}
        self._redis_conn.set(f'{self.cache_key}:{key}', value, **kwargs)
        self._touch_key(key)
        if self._implements_timeout:
            self._redis_conn.zadd(self._last_used_expiry_cache_name, {self._last_used_cache_name: time.time() + self.timeout})

    def delete(self, *keys: str) -> None:
        self._redis_conn.delete(*keys)
        self._redis_conn.zrem(self._last_used_cache_name, *keys)
        self._redis_conn.zrem(self._last_used_expiry_cache_name, *keys)

    def peek(self, key: str) -> str | int | bool | None:
        return self._redis_conn.get(self._to_redis_key(key))
