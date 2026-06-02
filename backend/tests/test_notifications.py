"""F6 in-app notifications: schema + service contract."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app.models.notification import NotificationKind
from app.schemas.notification import NotificationCreate


def test_notification_create_strips_and_validates_title():
    n = NotificationCreate(
        user_id=uuid4(),
        kind=NotificationKind.risk_created,
        title="  Drought warning  ",
        body="Rainfall below baseline.",
    )
    assert n.title == "Drought warning"
    assert n.body == "Rainfall below baseline."


def test_notification_create_rejects_oversized_fields():
    with pytest.raises(ValidationError):
        NotificationCreate(
            user_id=uuid4(),
            title="x" * 256,
            body="ok",
        )
    with pytest.raises(ValidationError):
        NotificationCreate(
            user_id=uuid4(),
            title="ok",
            body="x" * 2001,
        )


def test_notification_kind_enum_values():
    assert NotificationKind.risk_created.value == "risk_created"
    assert NotificationKind.yield_ready.value == "yield_ready"
    assert NotificationKind.snapshot_low_ndvi.value == "snapshot_low_ndvi"
    assert NotificationKind.system.value == "system"


def test_notification_out_from_attributes_roundtrip():
    from app.schemas.notification import NotificationOut

    fake = {
        "id": uuid4(),
        "user_id": uuid4(),
        "kind": NotificationKind.system,
        "title": "Welcome",
        "body": "Thanks for joining",
        "related_farm_id": None,
        "related_risk_id": None,
        "read": False,
        "created_at": datetime.now(timezone.utc),
    }
    out = NotificationOut.model_validate(fake)
    assert out.title == "Welcome"
    assert out.read is False
