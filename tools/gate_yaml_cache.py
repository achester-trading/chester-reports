"""
A gate's YAML parse cache: each distinct config text is parsed once per gate
process. (B97, 31 Oct 2026)

    import gate_yaml_cache
    gate_yaml_cache.install()

Why. A full edition reads its configuration as it builds: one Monthly build
calls yaml.safe_load 136 times over the same files, in pure-Python PyYAML, and
that is about 97% of the build's 20 seconds on the laptop. A gate that builds a
dozen editions parses the same unchanged files hundreds of times.

What it does not change. The cache is keyed on the TEXT handed to the parser
(a stream is read first), so a file that changes between two reads is parsed
again, and a different text can never be served another's result. Every hit
returns a deep copy, so a caller that mutates what it loaded mutates its own
copy, exactly as with a fresh parse. A text the parser refuses raises the same
error every time, because a refusal is never cached. Only yaml.safe_load is
wrapped; the parser itself, its loader and every other entry point are
untouched. Nothing outside the gate's own process sees it, and no report path
imports it.
"""

from __future__ import annotations

import copy

_CACHE: dict = {}
_ORIG = None


def _cached_safe_load(stream):
    text = stream.read() if hasattr(stream, "read") else stream
    try:
        key = (type(text), text)
        hash(key)
    except TypeError:
        return _ORIG(text)
    if key not in _CACHE:
        _CACHE[key] = _ORIG(text)
    return copy.deepcopy(_CACHE[key])


def install() -> None:
    """Wrap yaml.safe_load for the rest of this process. Idempotent."""
    global _ORIG
    import yaml                                                 # noqa: PLC0415
    if _ORIG is None:
        _ORIG = yaml.safe_load
        yaml.safe_load = _cached_safe_load


def stats() -> int:
    """How many distinct texts have been parsed."""
    return len(_CACHE)
