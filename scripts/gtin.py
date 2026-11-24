#!/usr/bin/env python3
"""Validate and normalise GTINs (UPC-A, EAN-8, EAN-13/JAN, GTIN-14). JSON output. Offline, stdlib only.

Usage: gtin.py CODE [CODE ...]
"""
from __future__ import annotations

import json
import re
import sys

TYPES = {8: "EAN-8", 12: "UPC-A", 13: "EAN-13/JAN", 14: "GTIN-14"}


def check_digit(body: str) -> int:
    total = sum(int(c) * (3 if i % 2 == 0 else 1) for i, c in enumerate(reversed(body)))
    return (10 - total % 10) % 10


def inspect(raw: str) -> dict:
    code = re.sub(r"[\s-]", "", raw)
    out: dict = {"input": raw, "code": code}
    if not re.fullmatch(r"[0-9]+", code) or len(code) not in TYPES:
        return {**out, "valid": False, "error": "not 8, 12, 13 or 14 digits"}
    valid = check_digit(code[:-1]) == int(code[-1])
    out.update(type=TYPES[len(code)], valid=valid)
    if valid:
        out["gtin14"] = code.zfill(14)
    if len(code) == 12:
        out["if_truncated_ean13"] = code + str(check_digit(code))
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    print(json.dumps([inspect(a) for a in sys.argv[1:]], indent=2))
