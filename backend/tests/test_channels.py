"""F13 channels MVP scaffold tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.channels import WhatsAppInbound, WhatsAppOutbound


def test_openapi_exposes_whatsapp_inbound():
    from app.main import app

    spec = app.openapi()
    assert "/api/v1/channels/whatsapp/inbound" in spec["paths"]
    assert "post" in spec["paths"]["/api/v1/channels/whatsapp/inbound"]


def test_whatsapp_inbound_strips_message():
    msg = WhatsAppInbound(From="whatsapp:+1234567890", Body="  Hello!  ")
    assert msg.Body == "Hello!"


def test_whatsapp_inbound_rejects_oversized_message():
    with pytest.raises(ValidationError):
        WhatsAppInbound(From="whatsapp:+1234567890", Body="x" * 4001)


def test_whatsapp_inbound_rejects_empty_message():
    with pytest.raises(ValidationError):
        WhatsAppInbound(From="whatsapp:+1234567890", Body="")


def test_whatsapp_outbound_shape():
    out = WhatsAppOutbound(to="whatsapp:+1234567890", body="Hi")
    assert out.channel == "whatsapp"
    assert out.body == "Hi"
