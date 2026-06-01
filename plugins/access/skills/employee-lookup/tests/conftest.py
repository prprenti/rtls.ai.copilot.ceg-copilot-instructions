"""Conftest for employee_lookup tests — adds the employee_lookup skill dir to sys.path."""

from __future__ import annotations

import os
import sys

# Ensure employee_lookup modules can be imported by their bare names
_cdis_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _cdis_dir not in sys.path:
    sys.path.insert(0, _cdis_dir)
