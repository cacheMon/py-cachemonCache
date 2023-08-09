# import sys
# import time


# from typing import Callable, Optional, Any, List, Tuple, Dict, Union
# from .cache import Cache


# # Class for the doubly-linked-list node objects.
# class S3FIFOValueNode(ValueError):
#     __slots__ = ("key", "value", "exp_time", "visited")

#     def __init__(self):
#         self.key = None
#         self.value = None
#         self.exp_time = sys.maxsize


# class S3FIFO(Cache):
#     def __init__(
#         self,
#         cache_size: int,
#         flash_mb: int = 0,
#         flash_path: str = None,
#         ttl_sec: int = sys.maxsize,
#         callback: Callable = None,
#         *args,
#         **kwargs
#     ):
#         super().__init__(cache_size, flash_mb, flash_path, ttl_sec, callback, *args, **kwargs)

#         small_fifo_size_ratio = kwargs.get("small_fifo_size_ratio", 0.1)
#         small_fifo_size = int(cache_size * small_fifo_size_ratio)
#         large_fifo_size = cache_size - small_fifo_size

#         self.small_fifo = [S3FIFOValueNode() for _ in range(small_fifo_size)]
#         self.large_fifo = [S3FIFOValueNode() for _ in range(large_fifo_size)]
#         self.ghost_fifo = [S3FIFOValueNode() for _ in range(small_fifo_size)]

#         if self.flash_mb > 0 or self.flash_path is not None:
#             raise ValueError("S3FIFO is the only supported flash cache")

#     def put(self, key: Any, value: Any, ttl_sec: int = sys.maxsize) -> None:
#         """insert a key value pair into the cache
#         if the key is in the cache, the value will be updated
#         """

#         if key in self.table:
#             node = self.table[key]

#             # Replace the value.
#             node.key = key
#             node.value = value
#             node.exp_time = time.time() + ttl_sec

#             return

#         node = S3FIFOValueNode()
#         node.key = key
#         node.value = value
#         node.exp_time = time.time() + ttl_sec
#         node.visited = False

#         # Add the node to the dictionary under the new key.
#         self.table[key] = node

#         self.prepend_to_head(node)

#         if len(self.table) > self.size:
#             self.evict()

#     def evict(self) -> Any:
#         """evict an object from the cache

#         Returns:
#             the evicted key
#         """

#         assert self.tail is not None

#         key_to_evict = self.tail.key
#         if self.eviction_callback is not None:
#             self.eviction_callback(self.tail.key, self.tail.value)

#         del self.table[key_to_evict]
#         self.tail = self.tail.prev
#         if self.tail is not None:
#             self.tail.next = None
#         else:
#             self.head = None

#         return key_to_evict

#     def get(self, key, default=None):
#         node = self.get_base(key, default)

#         if node is None:
#             return default

#         return node.value

#     def delete(self, key: Any) -> None:
#         """remove the key from the cache

#         Args:
#             key (Any): the key to remove
#         """

#         node = self.table[key]

#         if node is not None:
#             self.remove_from_list(node)
#             del self.table[key]

#     # Increases the size of the cache by inserting n empty nodes at the tail
#     # of the list.
#     def prepend_to_head(self, node):
#         if self.head is None:
#             assert self.tail is None
#             self.head = node
#             self.tail = node
#             node.next = None
#             node.prev = None

#             return

#         node.next = self.head
#         node.prev = None
#         self.head.prev = node
#         self.head = node

#     def remove_from_list(self, node):
#         if node.prev is not None and node.next is not None:
#             node.prev.next = node.next
#             node.next.prev = node.prev

#         if self.head == node:
#             self.head = node.next
#         if self.tail == node:
#             self.tail = node.prev