# adopted from pylru

# Cache implementaion with a Least Recently Used (LRU) replacement policy and
# a basic dictionary interface.

# Copyright (C) 2006-2022 Jay Hutchinson

# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.

# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.

# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


# The cache is implemented using a combination of a python dictionary (hash
# table) and a circular doubly linked list. Items in the cache are stored in
# nodes. These nodes make up the linked list. The list is used to efficiently
# maintain the order that the items have been used in. The front or head of
# the list contains the most recently used item, the tail of the list
# contains the least recently used item. When an item is used it can easily
# (in a constant amount of time) be moved to the front of the list, thus
# updating its position in the ordering. These nodes are also placed in the
# hash table under their associated key. The hash table allows efficient
# lookup of values by key.

import sys
import time


from typing import Callable, Optional, Any, List, Tuple, Dict, Union
from .cache import Cache


# Class for the doubly-linked-list node objects.
class LRUValueNode(ValueError):
    __slots__ = ("key", "value", "exp_time", "prev", "next")

    def __init__(self):
        self.key = None
        self.value = None
        self.exp_time = sys.maxsize
        self.next = None
        self.prev = None

    def __str__(self) -> str:
        return (
            "LRUValueNode(key: {}, value: {}, exp_time: {}, prev {}, next {})".format(
                self.key, self.value, self.exp_time, self.prev is not None, self.next is not None
            )
        )

    def __repr__(self) -> str:
        return self.__str__()

class LRU(Cache):
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
        """ create a LRU cache

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
            cache_size, dram_size_mb, flash_size_mb, flash_path, ttl_sec, eviction_callback, *args, **kwargs
        )

        self.head = None
        self.tail = None

        if flash_size_mb > 0 or flash_path is not None:
            raise ValueError("S3FIFO is the only supported flash cache")

    def put(self, key: Any, value: Any, ttl_sec: int = sys.maxsize // 10) -> None:
        """insert a key value pair into the cache
        if the key is in the cache, the value will be updated
        """

        self.n_put += 1

        if key in self.table:
            node = self.table[key]

            # Replace the value.
            node.key = key
            node.value = value
            node.exp_time = time.time() + ttl_sec

            # Update the list ordering.
            self.remove_from_list(node)
            self.prepend_to_head(node)

            return

        node = LRUValueNode()
        node.key = key
        node.value = value
        node.exp_time = time.time() + ttl_sec

        # Add the node to the dictionary under the new key.
        self.table[key] = node

        self.prepend_to_head(node)

        if len(self.table) > self.cache_size:
            self.evict()

    def get(self, key, default=None):
        self.n_get += 1

        if key not in self.table:
            return default

        node = self.table[key]
        self.remove_from_list(node)

        if node.exp_time < time.time():
            del self[key]
            return default

        self.prepend_to_head(node)

        self.n_hit += 1
        return node.value

    def evict(self) -> Any:
        """evict an object from the cache

        Returns:
            the evicted key
        """

        self.n_evict += 1

        assert self.tail is not None

        key_to_evict = self.tail.key
        if self.eviction_callback is not None:
            self.eviction_callback(self.tail.key, self.tail.value)

        del self.table[key_to_evict]
        self.tail = self.tail.prev
        if self.tail is not None:
            self.tail.next = None
        else:
            self.head = None

        return key_to_evict

    def delete(self, key: Any) -> None:
        """remove the key from the cache

        Args:
            key (Any): the key to remove
        """

        self.n_delete += 1

        node = self.table[key]

        if node is not None:
            self.remove_from_list(node)
            del self.table[key]

    # Increases the size of the cache by inserting n empty nodes at the tail
    # of the list.
    def prepend_to_head(self, node):
        if self.head is None:
            assert self.tail is None
            self.head = node
            self.tail = node
            node.next = None
            node.prev = None

            return

        node.next = self.head
        node.prev = None
        self.head.prev = node
        self.head = node

    def remove_from_list(self, node):
        if node.prev is not None:
            node.prev.next = node.next
        if node.next is not None:
            node.next.prev = node.prev

        if self.head == node:
            self.head = node.next
        if self.tail == node:
            self.tail = node.prev

    def __repr__(self):
        data = []
        node = self.head
        while node:
            data.append(str(node))
            assert len(data) <= self.cache_size
            node = node.next
        
        return "\n".join(data)
    
    def __str__(self) -> str:
        return self.__repr__()

