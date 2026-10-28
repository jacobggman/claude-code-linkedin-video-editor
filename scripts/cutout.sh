#!/bin/sh
# Kept so older installs and notes that say `zsh cutout.sh <project>` keep working. The real script is cutout.py,
# which runs on macOS, Linux and Windows:   python3 cutout.py <project_dir>
here=$(cd "$(dirname "$0")" && pwd)
for py in python3 python; do
  # run it once first: on Windows `python3` can be a Store stub that exists but is not a Python
  if "$py" -c "import sys" >/dev/null 2>&1; then exec "$py" "$here/cutout.py" "$@"; fi
done
echo "Python not found: run setup.py first"
exit 1
