import sys
import time

if sys.version_info < (3, 3):
    from collections import Mapping
else:
    from collections.abc import Mapping

from typing import Callable, Optional, Any, List, Tuple, Dict, Union


class Cache(object):
    def __init__(
        self,
        name: str,
        cache_size: int,
        dram_size_mb: int,
        flash_size_mb: int,
        flash_path: str,
        ttl_sec: int,
        eviction_callback: Callable,
    ) -> None:
        """create a cache object

        Args:
            cache_size (int): the size of the cache in objects
            dram_size_mb (int): the dram size in MB, if specified, cache_size (in objects) is ignored
            flash_size_mb (int): the flash size in MB
            flash_path (str): the path to a file on the flash
            ttl_sec (int): the default retention time in seconds, objects inserted into the cache will expire after this time
            eviction_callback (Callable): a callback function that will be called when an object is evicted from the cache
        """

        self.name = name
        self.cache_size = cache_size
        self.dram_size_byte = dram_size_mb * 1024 * 1024
        self.flash_size_byte = flash_size_mb * 1024 * 1024
        self.flash_path = flash_path
        self.ttl_sec = ttl_sec
        self.eviction_callback = eviction_callback

        self.n_get = 0
        self.n_hit = 0
        self.n_put = 0
        self.n_delete = 0
        self.n_evict = 0

        # Create an empty hash table.
        self.table = {}

    def __len__(self):
        return len(self.table)

    def __contains__(self, key):
        return key in self.table

    def __getitem__(self, key):
        value = self.get(key, None)
        if value is None:
            raise KeyError(key)
        return value

    def clear(self):
        self.table.clear()

    def __setitem__(self, key, value):
        self.put(key, value, self.ttl_sec)

    def __delitem__(self, key):
        self.delete(key)

    def __iter__(self):
        for key, node in self.table.items():
            yield key

    def items(self):
        for key, node in self.table.items():
            yield key, node.value

    def keys(self):
        # Return an iterator that returns the keys in the cache in order from
        # the most recently to least recently used. Does not modify the cache's
        # order.
        for key in self.table.keys():
            yield key

    def values(self):
        # Return an iterator that returns the values in the cache in order
        # from the most recently to least recently used. Does not modify the
        # cache's order.
        for node in self.table.values():
            yield node.value

    def update(self, *args, **kwargs):
        """update the cache"""

        if len(args) > 0:
            other = args[0]
            if isinstance(other, Mapping):
                for key in other:
                    self[key] = other[key]
            elif hasattr(other, "keys"):
                for key in other.keys():
                    self[key] = other[key]
            else:
                for key, value in other:
                    self[key] = value

        for key, value in kwargs.items():
            self[key] = value

    def add_eviction_callback(self, eviction_callback):
        self.eviction_callback = eviction_callback

    def __repr__(self):
        for key, node in self.table.items():
            print("{:<8} {}".format(key, node))

    def __str__(self):
        return self.__repr__()

    # # The methods __getstate__() and __setstate__() are used to correctly
    # # support the copy and pickle modules from the standard library. In
    # # particular, the doubly linked list trips up the introspection machinery
    # # used by copy/pickle.
    # def __getstate__(self):
    #     # Copy the instance attributes.
    #     d = self.__dict__.copy()

    #     # Remove those that we need to do by hand.
    #     del d["table"]
    #     del d["head"]

    #     elements = [(node.key, node.value) for node in self.table.items()]
    #     return (d, elements)

    # def __setstate__(self, state):
    #     d = state[0]
    #     elements = state[1]

    #     # Restore the instance attributes, except for the table and head.
    #     self.__dict__.update(d)

    #     # Setup a table and double linked list. This is identical to the way
    #     # __init__() does it.
    #     self.table = {}

    #     self.head = LRUValueNode()
    #     self.head.next = self.head
    #     self.head.prev = self.head

    #     for key, value in reversed(elements):
    #         self[key] = value

    def put(self, key, value, ttl_sec):
        raise NotImplementedError

    def delete(self, key):
        raise NotImplementedError

    def evict(self):
        raise NotImplementedError

    def get(self, key, default=None):
        raise NotImplementedError
