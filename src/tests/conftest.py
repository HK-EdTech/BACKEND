import os
import sys

# Make "ai_agents.*", "common.*" and "utils.*" importable, matching PYTHONPATH=src in tox.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
