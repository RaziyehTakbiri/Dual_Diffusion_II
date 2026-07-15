"""Convert Databricks source-format notebooks (.py) to .ipynb twins.

Every milestone driver notebook is authored as Databricks source (.py, good
for review/versioning); this utility emits an .ipynb with identical cells for
anyone who prefers importing classic Jupyter files.

Usage: python notebooks/_to_ipynb.py            (converts all .py here)
"""

from __future__ import annotations

import json
import pathlib
import sys

MARKER = "# Databricks notebook source"
SPLIT = "# COMMAND ----------"
MAGIC = "# MAGIC "


def to_cells(src: str):
    body = src.split(MARKER, 1)[-1]
    for chunk in body.split(SPLIT):
        lines = chunk.strip("\n").splitlines()
        if not any(l.strip() for l in lines):
            continue
        stripped = [l for l in lines if l.strip()]
        if all(l.startswith("# MAGIC") for l in stripped):
            content = "\n".join(l[len(MAGIC):] if l.startswith(MAGIC) else ""
                                for l in lines)
            if content.lstrip().startswith("%md"):
                text = content.lstrip()[3:].lstrip("\n")
                yield {"cell_type": "markdown", "metadata": {},
                       "source": text.splitlines(keepends=True)}
            else:  # %pip etc. stay as code-cell magics
                yield {"cell_type": "code", "metadata": {}, "outputs": [],
                       "execution_count": None,
                       "source": content.splitlines(keepends=True)}
        else:
            yield {"cell_type": "code", "metadata": {}, "outputs": [],
                   "execution_count": None,
                   "source": chunk.strip("\n").splitlines(keepends=True)}


def convert(path: pathlib.Path) -> pathlib.Path:
    src = path.read_text()
    if not src.lstrip().startswith(MARKER):
        raise ValueError(f"{path} is not Databricks source format")
    nb = {
        "cells": list(to_cells(src)),
        "metadata": {"language_info": {"name": "python"}},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    out = path.with_suffix(".ipynb")
    out.write_text(json.dumps(nb, indent=1))
    return out


if __name__ == "__main__":
    here = pathlib.Path(__file__).parent
    targets = [p for p in sorted(here.glob("*.py")) if not p.name.startswith("_")]
    if not targets:
        sys.exit("no notebooks found")
    for p in targets:
        print(f"{p.name} -> {convert(p).name}")
