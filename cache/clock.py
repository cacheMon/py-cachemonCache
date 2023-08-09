import sys
import time


from typing import Callable, Optional, Any, List, Tuple, Dict, Union
from .cache import Cache


# Class for the doubly-linked-list node objects.
class ClockValueNode(ValueError):
    __slots__ = ("key", "value", "exp_time", "visited")

    def __init__(self):
        self.key = None
        self.value = None
        self.exp_time = sys.maxsize
        self.visited = False


class Clock(Cache):
    def __init__(
        self,
        cache_size: int,
        flash_mb: int = 0,
        flash_path: str = None,
        ttl_sec: int = sys.maxsize,
        callback: Callable = None,
        *args,
        **kwargs
    ):
        super().__init__(
            cache_size, flash_mb, flash_path, ttl_sec, callback, *args, **kwargs
        )

        self.clock_buffer = [ClockValueNode() for _ in range(cache_size)]
        self.clock_pointer = 0

        if self.flash_mb > 0 or self.flash_path is not None:
            raise ValueError("S3Clock is the only supported flash cache")

    def _find_next_available_slot(self):
        while self.clock_buffer[self.clock_pointer].visited:
            self.clock_buffer[self.clock_pointer].visited = False
            self.clock_pointer = (self.clock_pointer + 1) % self.cache_size

    def put(self, key: Any, value: Any, ttl_sec: int = sys.maxsize) -> None:
        """insert a key value pair into the cache
        if the key is in the cache, the value will be updated
        """

        if key in self.table:
            buf_idx = self.table[key]
            node = self.clock_buffer[buf_idx]

            # Replace the value.
            node.key = key
            node.value = value
            node.visited = True
            node.exp_time = time.time() + ttl_sec

            return

        node = ClockValueNode()
        node.key = key
        node.value = value
        node.exp_time = time.time() + ttl_sec

        self._find_next_available_slot()
        if self.clock_buffer[self.clock_pointer].key is not None:
            self.evict()

        self.clock_buffer[self.clock_pointer] = node
        self.table[key] = self.clock_pointer
        self.clock_pointer = (self.clock_pointer + 1) % self.cache_size

    def get(self, key, default=None):
        if key not in self.table:
            return default

        node_idx = self.table[key]
        node = self.clock_buffer[node_idx]
        node.visited = True

        if node.exp_time < time.time():
            del self[key]
            node.key = None
            node.value = None
            return default

        return node.value

    def evict(self) -> Any:
        """evict an object from the cache

        Returns:
            the evicted key
        """

        assert self.clock_buffer[self.clock_pointer].key is not None

        node = self.clock_buffer[self.clock_pointer]
        key_to_evict = node.key
        if self.eviction_callback is not None:
            self.eviction_callback(node.key, node.value)

        del self.table[key_to_evict]

        return key_to_evict

    def delete(self, key: Any) -> None:
        """remove the key from the cache

        Args:
            key (Any): the key to remove
        """

        node_idx = self.table[key]

        if node_idx is not None:
            self.clock_buffer[node_idx].key = None
            self.clock_buffer[node_idx].value = None
            self.clock_buffer[node_idx].exp_time = sys.maxsize
            self.clock_buffer[node_idx].visited = False
            del self.table[key]

    def items(self):
        for key, node_idx in self.table.items():
            yield key, self.clock_buffer[node_idx].value

    def values(self):
        for node_idx in self.table.values():
            yield self.clock_buffer[node_idx].value
