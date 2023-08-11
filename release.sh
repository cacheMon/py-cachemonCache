#!/bin/bash
set -eu

python3 -m pip install --upgrade build twine hatch > /dev/null

rm dist/* >/dev/null || true

hatch version patch
# hatch version minor
# hatch version major

python3 -m build

python3 -m twine upload --repository testpypi dist/*

# sleep 20
python3 -m pip install -U --index-url https://test.pypi.org/simple/ --no-deps cachemonCache

python3 -c "from cachemonCache import LRU; cache=LRU(100); cache.put('a', 1); print(cache.get('a'))"

twine upload dist/*


