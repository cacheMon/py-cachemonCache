import os
import sys
import struct
import csv

class traceReader:
    def __init__(self, trace_path: str, trace_format: str, n_max_req: int = -1):
        self.trace_path = trace_path
        self.trace_format = trace_format
        self.n_max_req = n_max_req
        self.n_read_req = 0
        self.trace_file = open(trace_path, "r")

    def read(self):
        raise NotImplementedError

    def __iter__(self):
        return self

    def __next__(self):
        data = self.read()
        if data is None:
            raise StopIteration
        else:
            return data

    def reset(self):
        self.trace_file.seek(0)
        self.n_read_req = 0

    

class traceReaderMeta(traceReader):
    def __init__(self, trace_path, n_max_req: int = -1):
        super().__init__(trace_path, "meta_kv_csv", n_max_req)
        self.trace_reader = csv.reader(self.trace_file, delimiter=" ")

    def read(self):
        try:
            return next(self.trace_reader)
        except StopIteration:
            self.trace_file.close()
            raise StopIteration


class traceReaderCSV(traceReader):
    def __init__(self, trace_path, n_max_req: int = -1):
        super().__init__(trace_path, "csv", n_max_req)
        self.trace_file.close()
        self.trace_file = open(trace_path, "r")
        self.trace_reader = csv.reader(self.trace_file)

    def read(self):
        # 0, 13053225291711363978, 737, 13
        line = next(self.trace_reader)
        if len(line) == 0:
            return None

        return line[:3]


class traceReaderLibcachesim(traceReader):
    def __init__(self, trace_path, n_max_req: int = -1):
        super().__init__(trace_path, "libcachesim", n_max_req)
        self.trace_file = open(trace_path, "rb")
        self.s = struct.Struct("<IQIQ")

    def read(self):
        b = self.trace_file.read(self.s.size)
        if len(b) == 0:
            return None

        if self.n_read_req >= self.n_max_req and self.n_max_req > 0:
            return None

        self.n_read_req += 1

        return self.s.unpack(b)[:3]

    # def reset(self):
    #     self.trace_file.seek(0)
    #     self.n_read_req = 0

if __name__ == "__main__":
    import os
    import sys

    BASEPATH = os.path.dirname(os.path.abspath(__file__)) + "/../"
    reader = traceReaderLibcachesim(
        "{}/data/cloudphysics.oracleGeneral.bin".format(BASEPATH),
        1000,
    )

    for r in reader:
        print(r)
