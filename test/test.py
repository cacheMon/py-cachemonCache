import sys
import os
import time

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../"))
from cache import *
from cache.cacheDecorator import cacheDecorator

import random
import unittest


def test_cache_basic(cache, cache_size):
    """test basic get and set functions"""

    data_true = []
    # insert data
    for i in range(cache_size // 2):
        cache.put(i, i)
        cache.put(str(i), str(i))
        data_true.append((i, i))
        data_true.append((str(i), str(i)))

    assert tuple(cache.items()) == tuple(data_true), "{} == {}".format(
        tuple(cache.items()), tuple(data_true)
    )

    # test get
    for i in range(cache_size // 2):
        assert cache.get(i) == i, "{} == {}".format(i, cache.get(i))
        assert cache.get(str(i)) == str(i), "{} == {}".format(i, cache.get(i))

    # test eviction
    for i in range(cache_size):
        cache.put(str(i * 10) + "a", i)
        assert cache[str(i * 10) + "a"] == i, "{} == {}".format(cache[str(i)], i)

    # test new data
    for i in range(cache_size):
        assert cache[str(i * 10) + "a"] == i, "{} == {}".format(cache[str(i)], i)

    cache.put("test", "test")
    assert cache["test"] == "test"
    assert cache.get("test") == "test"
    assert cache.get("test2") == None
    assert cache.get("0", "default") == "default"


def test_cache_callback(cache, cache_size):
    """test cache callback function"""

    evicted_data = {}

    def callback(key, value):
        evicted_data[key] = value

    cache.add_eviction_callback(callback)

    for i in range(cache_size):
        cache.put(i, i)

    for i in range(cache_size):
        cache[str(i + 1)] = i * 10

    assert len(evicted_data) == cache_size, "{} == {}".format(
        len(evicted_data), cache_size
    )
    assert sorted(evicted_data.keys()) == list(range(cache_size)), "{} == {}".format(
        sorted(evicted_data.keys()), list(range(cache_size))
    )


def test_cache_ttl(cache, cache_size):
    """test basic get and set functions"""

    cache["test"] = "test"
    cache.put("test2", "test2", 1)
    cache.put("test4", "test4", 20)
    assert cache["test"] == "test"
    time.sleep(2)

    assert cache.get("test2") == None, "test2 should have expired, {} == {}".format(
        cache.get("test2"), None
    )
    assert cache.get("test2", "default") == "default", "{} == {}".format(
        cache.get("test2"), None
    )
    try:
        cache["test2"]
    except KeyError:
        pass
    else:
        assert False, "KeyError not raised"

    assert cache.get("test4") == "test4", "{} == {}".format(cache.get("test4"), "test4")


class TestLRUCacheBasic(unittest.TestCase):
    cache_size = 8

    def setUp(self):
        self.cache = LRU(self.cache_size)
        self.cache_size = self.cache_size

    def tearDown(self):
        pass

    def test_cache_semantics(self):
        for i in range(self.cache_size):
            self.cache.put(i, i)

        for i in range(self.cache_size // 2):
            self.cache.get(i)

        for i in range(self.cache_size // 2):
            self.cache.put(i * 10, i * 10)

        for i in range(self.cache_size // 2):
            self.assertTrue(i in self.cache)

        self.cache.put("test", "test")
        for i in range(self.cache_size - 1):
            self.cache.put(i, i)
        self.assertTrue("test" in self.cache)

        self.cache.get("test", "test")
        for i in range(self.cache_size - 1):
            self.cache.put(i * 20, i)
        self.assertTrue("test" in self.cache)


class TestClockCacheBasic(unittest.TestCase):
    cache_size = 8

    def setUp(self):
        self.cache = Clock(self.cache_size)
        self.cache_size = self.cache_size

    def tearDown(self):
        pass

    def test_cache_semantics(self):
        pass


@cacheDecorator(100, eviction="LRU")
def square(x):
    return x * x


def testDecorator():
    for i in range(1000):
        x = random.randint(0, 200)
        assert square(x) == x * x, "{} == {}".format(square(x), x * x)


if __name__ == "__main__":
    random.seed()

    cache_size = 20
    for cache_type in [FIFO, LRU, Clock, S3FIFO]:
    # for cache_type in [S3FIFO]:
        print("Testing {}".format(cache_type.__name__))
        test_cache_basic(cache_type(cache_size), cache_size)
        test_cache_callback(cache_type(cache_size), cache_size)
        test_cache_ttl(cache_type(cache_size), cache_size)

    testDecorator()

    unittest.main()

