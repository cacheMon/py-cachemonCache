import os
import sys
import time

BASEPATH = os.path.dirname(os.path.abspath(__file__)) + "/../"
sys.path.append(BASEPATH)
from cache import *
from bench.trace_reader import traceReaderLibcachesim, traceReaderCSV


def run_trace(cache, reader):
    start_time = time.time()

    n_req, n_miss = 0, 0
    for r in reader:
        _timestamp, obj_id, _size = r
        n_req += 1
        if not cache.get(obj_id):
            n_miss += 1
            cache.put(obj_id, obj_id)

    end_time = time.time()
    print(
        "trace {} {:16}, miss ratio {:.4f}, throughput {:.4f} req/s".format(
            os.path.basename(reader.trace_path),
            cache.name,
            n_miss / n_req,
            n_req / (end_time - start_time),
        )
    )


if __name__ == "__main__":
    reader1, cache_size1 = (
        traceReaderLibcachesim(
            "{}/data/cloudphysics.oracleGeneral.bin".format(BASEPATH),
        ),
        12000,
    )

    reader2, cache_size2 = (
        traceReaderCSV("{}/data/twitter_cluster52_10m.csv".format(BASEPATH)),
        10000,
    )

    reader = reader2
    cache_size = cache_size2

    for cache_type in [
        FIFO,
        LRU,
        Clock,
        S3FIFO,
    ]:
        run_trace(cache_type(cache_size), reader)
        reader.reset()
