# lambda/vanity/tests/test_handler_local.py
from unittest.mock import patch, MagicMock
from app.handler import handler

def test_handler_returns_options_without_connect():
    event = {"phone": "+13035551212"}
    fake_ctx = MagicMock()

    # Patch the ddb table reference inside app.handler
    with patch("app.handler.table") as mock_table:
        mock_table.put_item.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}
        res = handler(event, fake_ctx)

    # Ensure keys exist
    assert "option1" in res
    assert "option2" in res
    assert "option3" in res