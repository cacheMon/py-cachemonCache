"""
    an implementation of S3FIFO cache
       this is not the most efficient implementation
"""

import sys
import time
from collections import deque

from typing import Callable, Optional, Any, List, Tuple, Dict, Union
from .cache import Cache


# Class for the doubly-linked-list node objects.
class S3FIFOValueNode:
    __slots__ = ("key", "value", "exp_time", "freq")

    def __init__(self):
        self.key = None
        self.value = None
        self.exp_time = sys.maxsize
        # use freq -1 to indicate ghost entry and deleted entry
        self.freq = 0

    def __str__(self) -> str:
        return "S3FIFOValueNode(key: {}, value: {}, exp_time: {}, freq {})".format(
            self.key, self.value, self.exp_time, self.freq
        )

    def __repr__(self) -> str:
        return self.__str__()


class S3FIFO(Cache):
    def __init__(
        self,
        cache_size: int,
        dram_size_mb: int = 0,
        flash_size_mb: int = 0,
        flash_path: str = None,
        ttl_sec: int = sys.maxsize // 10,
        eviction_callback: Callable = None,
        *args,
        **kwargs
    ):
        """create a S3FIFO cache

        Args:
            cache_size (int): cache size in objects
            dram_size_mb (int, optional): dram size in MB, if specified, cache_size will be ignored, currently not used. Defaults to 0.
            flash_size_mb (int, optional): flash size in MB. Defaults to 0.
            flash_path (str, optional): path to a file on the flash. Defaults to None.
            ttl_sec (int, optional): the default retention time. Defaults to sys.maxsize // 10.
            eviction_callback (Callable, optional): eviction callback. Defaults to None.

        Raises:
            ValueError: _description_
        """
        super().__init__(
            cache_size,
            dram_size_mb,
            flash_size_mb,
            flash_path,
            ttl_sec,
            eviction_callback,
            *args,
            **kwargs
        )

        self.small_to_main_threshold = kwargs.get("small_to_main_threshold", 1)
        self.small_fifo_size_ratio = kwargs.get("small_fifo_size_ratio", 0.1)
        self.small_fifo_size = int(cache_size * self.small_fifo_size_ratio)
        self.main_fifo_size = cache_size - self.small_fifo_size

        self.small_fifo = deque()
        self.main_fifo = deque()
        self.ghost_fifo = deque()
        self.curr_size = 0

        if flash_size_mb > 0 or flash_path is not None:
            raise ValueError("S3FIFO is the only supported flash cache")

    def put(self, key: Any, value: Any, ttl_sec: int = sys.maxsize // 10) -> None:
        """insert a key value pair into the cache
        if the key is in the cache, the value will be updated
        """

        self.n_put += 1

        if key in self.table:
            node = self.table[key]
            assert node.key == key

            # if key in the table, but freq is -1, it means the key is in the ghost
            # if the key is not in the table, but in the queue and freq is -1, it means the key is deleted
            if node.freq == -1:
                # if the node is in the ghost, mark it deleted in the ghost
                assert node.value is None
                node.key = None

                new_node = S3FIFOValueNode()
                new_node.key = key
                new_node.value = value
                new_node.exp_time = time.time() + ttl_sec

                # insert to the main
                self.main_fifo.append(new_node)
                self.table[key] = new_node
                self.curr_size += 1

            else:
                # Replace the value.
                node.value = value
                node.exp_time = time.time() + ttl_sec

        else:
            new_node = S3FIFOValueNode()
            new_node.key = key
            new_node.value = value
            new_node.exp_time = time.time() + ttl_sec

            self.table[key] = new_node
            self.small_fifo.append(new_node)
            self.curr_size += 1

        while self.curr_size > self.cache_size:
            self.evict()

    def evict_small(self) -> Any:
        while len(self.small_fifo) > 0:
            node = self.small_fifo.popleft()
            if node.freq == -1:
                # deleted entry
                assert node.key is None
                assert node.value is None
                del self.table[node.key]

            elif node.freq >= self.small_to_main_threshold:
                # insert to the main
                node.freq = 0
                self.main_fifo.append(node)
                if len(self.main_fifo) > self.main_fifo_size:
                    return self.evict_large()
            else:
                if self.eviction_callback is not None:
                    self.eviction_callback(node.key, node.value)
                # insert to the ghost
                node.freq = -1
                node.value = None
                self.ghost_fifo.append(node)
                while len(self.ghost_fifo) > self.main_fifo_size:
                    ghost_to_evict = self.ghost_fifo.popleft()
                    del self.table[ghost_to_evict.key]

                return node.key

    def evict_large(self) -> Any:
        while len(self.main_fifo) > 0:
            node = self.main_fifo.popleft()
            if node.freq == -1:
                # deleted entry
                assert node.key is None
                assert node.value is None
                del self.table[node.key]

            elif node.freq >= 1:
                node.freq -= 1
                self.main_fifo.append(node)

            else:
                if self.eviction_callback is not None:
                    self.eviction_callback(node.key, node.value)
                del self.table[node.key]
                return node.key

    def evict(self) -> Any:
        """evict an object from the cache

        Returns:
            the evicted key
        """

        self.n_evict += 1

        # print(
        #     "{}+{} evicting t{} c{}/{} s{} m{} g{}".format(
        #         self.n_get,
        #         self.n_put,
        #         len(self.table),
        #         self.curr_size,
        #         self.cache_size,
        #         len(self.small_fifo),
        #         len(self.main_fifo),
        #         len(self.ghost_fifo),
        #     )
        # )
        # print(self.main_fifo)

        self.curr_size -= 1
        if len(self.small_fifo) > self.small_fifo_size:
            return self.evict_small()
        else:
            return self.evict_large()

    def get(self, key, default=None):
        self.n_get += 1

        if key not in self.table:
            return default

        node = self.table[key]

        if node.exp_time < time.time():
            del self[key]
            node.freq = -1
            node.value = None
            node.key = None
            self.curr_size -= 1
            return default

        if node.freq == -1:
            assert node.value is None
            return default

        node.freq = min(node.freq + 1, 3)
        self.n_hit += 1
        return node.value

    def delete(self, key: Any) -> None:
        """remove the key from the cache

        Args:
            key (Any): the key to remove
        """

        self.n_delete += 1

        node = self.table[key]

        if node is not None:
            del self.table[key]
            node.value = None
            node.freq = -1
            node.key = None
            self.curr_size -= 1
