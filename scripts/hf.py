#!/usr/bin/env python3
"""HyperFrames launcher: one command that works the same in zsh, bash, Git Bash and PowerShell.

Usage (from the project folder):   PY hf.py <hyperframes arguments>
  PY hf.py lint
  PY hf.py snapshot --at 1.2,3.4,5.6 --no-end --describe false
  PY hf.py render -o renders/<slug>-v1.mp4 --quality high

Runs `npx --yes hyperframes@0.8.34 <arguments>` (the pinned version) with the Node 22+ that setup.py found first
on PATH, so there is no `nvm use`, and without a shell, so Windows' npx.cmd is not a problem. Standard library only.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skillenv  # noqa: E402

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(skillenv.run_hyperframes(sys.argv[1:]))
