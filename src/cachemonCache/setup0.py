
from setuptools import setup, Extension

# module1 = Extension('cachemon',
#                     sources = ['lru.c'])

setup (name = 'cachemon',
       version = '0.0.1',
       description = 'a cache library with dict interface',
       long_description = open('README.md').read(),
       long_description_content_type="text/x-md",
       author='Juncheng Yang',
       url='https://github.com/cachemon/cachemon-py',
       license='MIT',
       keywords='lru, cache, s3fifo, sieve, dict',
    #    ext_modules = [module1],
       classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Operating System :: POSIX',
        'Programming Language :: C',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Software Development :: Libraries :: Python Modules',
        ],
        extras_require={
            'test': ['pytest'],
        },
)


