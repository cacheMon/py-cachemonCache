# CachemonCache: A Python Package for Caching

CachemonCache is a package that provides efficient and fast caching in Python, including 
* Caching with different eviction algorithms, e.g., FIFO, LRU, [S3FIFO](), [Sieve]()
* Tiered caching using your flash
* Thread-safe caches for multi-threaded applications
<!-- * Optimized for machine-learning applications -->

It uses a similar interface as `dict` so it can be used as a drop-in replacement for Python dict to save space. 


## News 
* 2023-08-01: CachemonCache is under development!
<!-- * 2023-10-01: CachemonCache is released! -->



## Installation
```bash
pip install CachemonCache
```

## Usage
```python
# you can import FIFO, LRU, S3FIFO, Sieve
from cachemonCache import LRU
from cachemonCache import S3FIFO

# create a cache backed by DRAM, use S3FIFO eviction if you care about hit ratio
cache = LRU(size=10) # or cache = S3FIFO(size=10)

# create a cache backed by your local flash, size is the number of objects in DRAM cache
cache = S3FIFO(size=1000, flash_size_mb=1000, path="/disk/cachmon.data")

# put an item into the cache
cache.put("key", "value")  # or cache["key"] = "value"
# you can specify a TTL using cache.put("key", "value", ttl=10)

# get an item from the cache
cache.get("key")

# delete an item from the cache
cache.delete("key")  # or del cache["key"]

# check if an item is in the cache
"key" in cache  # or cache.has("key")

# get the size of the cache
len(cache)

# add a callback for eviction
def callback(key, value, *args, **kwargs):
    print("key: {}, value: {}".format(key, value))
cache.add_callback(callback)

# list all items in the cache
print(cache.items())  # or print(cache.keys())

# get some stat
print(cache.stats())  # or cache.miss_ratio()

```

Cachemon can also be used as a decorator to cache the return value of a function similar to the [functools](https://docs.python.org/3/library/functools.html) in standard library. 

```python
from cachemonCache import S3FIFO
@S3FIFO(size=1000, flash_size_mb=1000, path="/disk/cachmon.data")
def foo(x):
    return x + 1
```

## Benchmark
```bash
python3 src/cachemonCache/bench/benchmark.py

```



## Road map
1. support multi-threading
2. support flash


## Contributing
We welcome contributions to Cachemon! Please check out our [contributing guide](CONTRIBUTING.md) for more details. 



