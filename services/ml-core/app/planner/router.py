"""Platform router: URL fingerprint -> the adapter that owns this page.

Named adapters are tried first (most specific), then the generic ATS adapter as a
last resort. Adding a new ATS = add one adapter and register it here.
"""
from __future__ import annotations

from ..adapters.base import Adapter
from ..adapters.cutshort import CutshortAdapter
from ..adapters.generic import GenericATSAdapter
from ..adapters.greenhouse import GreenhouseAdapter
from ..adapters.lever import LeverAdapter
from ..adapters.linkedin import LinkedInAdapter
from ..adapters.workday import WorkdayAdapter

# URL substrings -> adapter. Order = priority (most specific first).
_FINGERPRINTS: list[tuple[list[str], Adapter]] = [
    (["linkedin.com"], LinkedInAdapter()),
    (["myworkdayjobs.com", "workday"], WorkdayAdapter()),
    (["greenhouse.io", "boards.greenhouse", "grnh.se"], GreenhouseAdapter()),
    (["lever.co"], LeverAdapter()),
    (["cutshort.io"], CutshortAdapter()),
]

_GENERIC = GenericATSAdapter()


def route(url: str) -> Adapter:
    low = (url or "").lower()
    for needles, adapter in _FINGERPRINTS:
        if any(n in low for n in needles):
            return adapter
    return _GENERIC
