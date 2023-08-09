import functools
from cache.fifo import FIFO
from cache.lru import LRU
from cache.clock import Clock
# from cache.s3fifo import S3FIFO
# from cache.sieve import Sieve


class cacheDecorator(object):
    def __init__(self, size, eviction="S3FIFO", callback=None):
        if eviction == "FIFO":
            self.cache = FIFO(size)
        elif eviction == "LRU":
            self.cache = LRU(size)
        elif eviction == "Clock":
            self.cache = Clock(size)
        # elif eviction == "S3FIFO":
        #     self.cache = S3FIFO(size)
        # elif eviction == "SIEVE":
        #     self.cache = Sieve(size)
        else:
            raise ValueError("invalid eviction policy {}".format(eviction))

        if callback is not None:
            self.cache.add_eviction_callback(callback)

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            kwtuple = tuple((key, kwargs[key]) for key in sorted(kwargs.keys()))
            key = (args, kwtuple)
            try:
                value = self.cache[key]
                return value
            except KeyError:
                pass

            value = func(*args, **kwargs)
            self.cache[key] = value
            return value

        wrapper.cache = self.cache
        wrapper.size = self.cache.cache_size
        wrapper.clear = self.cache.clear
        return functools.update_wrapper(wrapper, func)
