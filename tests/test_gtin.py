#!/usr/bin/env python3
"""Self-checks for GTIN validation. Run: python3 tests/test_gtin.py"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from gtin import inspect  # noqa: E402

assert inspect("036000291452")["valid"]
assert inspect("4006381333931")["valid"]
assert not inspect("4006381333932")["valid"]
assert inspect("4961310159672")["gtin14"] == inspect("04961310159672")["gtin14"]
assert inspect("496131015967")["if_truncated_ean13"] == "4961310159672"
assert not inspect("B0BRQNJG7X")["valid"]
print("ok")
