
import os
import sys
import struct


class traceReader():
    def __init__(self, trace_path, trace_format):
        self.trace_path = trace_path
        self.trace_format = trace_format
    
    def read(self):
        raise NotImplementedError
    
    def __iter__(self):
        return self
    
    def __next__(self):
        return self.read()


class traceReaderMeta(traceReader):
    def __init__(self, trace_path, trace_format):
        super().__init__(trace_path, trace_format)
        self.trace_file = open(trace_path, "r")
        self.trace_reader = csv.reader(self.trace_file, delimiter=" ")
        
        
    def read(self):
        try:
            return next(self.trace_reader)
        except StopIteration:
            self.trace_file.close()
            raise StopIteration
        
class traceReaderLibCacheSim(traceReader):
    def __init__(self, trace_path, trace_format):
        super().__init__(trace_path, trace_format)
        self.trace_file = open(trace_path, "r")
        self.trace_reader = csv.reader(self.trace_file, delimiter=" ")
    
    def read(self):
        pass




        