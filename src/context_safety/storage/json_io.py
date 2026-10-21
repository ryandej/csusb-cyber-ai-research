"""Bounded, strict UTF-8 JSON. Nothing here follows paths or URLs in input."""

import json
import math

MAX_BYTES = 1024 * 1024
MAX_DEPTH = 32
MAX_ELEMENTS = 20000


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _constant(value):
    raise ValueError(f"Nonfinite JSON number: {value}")


def strict_loads(payload: bytes | str):
    raw = payload.encode("utf-8", errors="strict") if isinstance(payload, str) else payload
    if len(raw) > MAX_BYTES:
        raise ValueError("JSON upload exceeds 1 MiB.")
    text = raw.decode("utf-8", errors="strict")
    # Check nesting before the JSON decoder can exhaust the interpreter stack.
    depth = 0
    quoted = escaped = False
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in "[{":
            depth += 1
            if depth > MAX_DEPTH:
                raise ValueError("JSON nesting exceeds 32 levels.")
        elif char in "]}":
            depth -= 1
    value = json.loads(text, object_pairs_hook=_pairs, parse_constant=_constant)
    stack = [value]
    count = 0
    while stack:
        item = stack.pop()
        count += 1
        if count > MAX_ELEMENTS:
            raise ValueError("JSON exceeds 20,000 parsed elements.")
        if isinstance(item, dict):
            stack.extend(item.keys())
            stack.extend(item.values())
        elif isinstance(item, list):
            stack.extend(item)
        elif isinstance(item, float) and not math.isfinite(item):
            raise ValueError("Nonfinite JSON number.")
        elif isinstance(item, str):
            item.encode("utf-8", errors="strict")  # Reject isolated surrogate escapes.
    return value


def canonical_bytes(value) -> bytes:
    """Sorted keys, two-space indent, literal UTF-8, final newline; no NaN."""
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2,
                       allow_nan=False) + "\n").encode("utf-8")


def load_bundle(payload: bytes | str):
    from context_safety.domain.models import Bundle
    from context_safety.domain.validation import validate_bundle
    from context_safety.review.eligibility import require_illustrative

    bundle = Bundle.model_validate(strict_loads(payload))
    validate_bundle(bundle)
    require_illustrative(bundle)
    return bundle


def export_bundle(bundle) -> bytes:
    # Revalidate at every application entry point, including mutated nested lists.
    encoded = canonical_bytes(bundle.model_dump(mode="json"))
    load_bundle(encoded)
    return encoded
