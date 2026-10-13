"""Regression tests for ledger tampering, immutable snapshots, and validation."""
import pytest
from pydantic import ValidationError

from agents.base import AuditTrail, SecurityException
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor


def test_audit_signature_tampering_detected():
    trail = AuditTrail(secret_key="test-only-key")
    trail.log("worker", "routine", "START", {"sample": "anonymous"})
    trail.log("worker", "routine", "DONE", {"sample": "anonymous"})
    assert trail.verify_integrity()
    trail.logs[-1]["event_type"] = "FORGED"
    assert not trail.verify_integrity()


def test_audit_snapshot_cannot_mutate_internal_trail():
    trail = AuditTrail(secret_key="test-only-key")
    trail.log("worker", "routine", "CHECK", {"sample": "anonymous"})
    snapshot = trail.get_trail()
    snapshot[0]["payload_hash"] = "invalid"
    assert trail.verify_integrity()


def test_supervisor_rejects_phi_in_attributes():
    payload = SystemTaskPayload(
        task_id="TEST", target_identifier="KEY-01",
        primary_metric=1.0, attributes={"contact": "alice@example.com"},
    )
    with pytest.raises(SecurityException):
        SystemSupervisor().process_task(payload)


def test_nonfinite_metrics_rejected():
    with pytest.raises(ValidationError):
        SystemTaskPayload(task_id="TEST", target_identifier="KEY-01",
                          primary_metric=float("nan"))
