"""Content hashes are integrity checks, not proof of authority or authorship."""

import hashlib

from context_safety.storage.json_io import canonical_bytes


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def record_digests(bundle) -> dict[str, str]:
    return {record.record_id: sha256(canonical_bytes(record.model_dump(mode="json")))
            for record in bundle.records()}


def verify_manifest(bundle) -> None:
    expected = record_digests(bundle)
    if bundle.manifest.record_digests != expected:
        raise ValueError("Manifest member digests do not match the exact records.")


def artifact_manifest(payload: bytes) -> dict:
    return {"schema_version": "0.3.0", "artifact": "bundle.json",
            "sha256": sha256(payload), "bytes": len(payload),
            "mode": "illustrative_deterministic"}
