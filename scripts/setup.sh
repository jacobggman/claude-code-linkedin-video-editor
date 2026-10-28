#!/bin/sh
# Kept so older installs and notes that say `zsh setup.sh` keep working. The real first-run check is setup.py,
# which runs on macOS, Linux and Windows:   python3 setup.py   (Windows: python setup.py, or py -3 setup.py)
# setup.py carries the version pins and the repair of a venv that already has PyAV 19 (see REQUIREMENTS there),
# so this wrapper does what the old script did.
here=$(cd "$(dirname "$0")" && pwd)
for py in python3 python; do
  # run it once first: on Windows `python3` can be a Store stub that exists but is not a Python
  if "$py" -c "import sys" >/dev/null 2>&1; then exec "$py" "$here/setup.py" "$@"; fi
done
echo "STATUS python MISSING -> install Python 3.10+ (Mac: brew install python | Linux: sudo apt install python3 python3-venv | Windows: winget install --id Python.Python.3.12 -e)"
echo "NOT READY"
exit 1
