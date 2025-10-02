# lambda/vanity/tests/test_handler_local.py
from unittest.mock import patch, MagicMock
from lambda.vanity.handler import handler

def test_handler_returns_options_without_connect():
    event = {"phone": "+13035551212"}
    fake_ctx = MagicMock()

    # Patch the ddb table's put_item so we don't hit AWS
    with patch("lambda.vanity.handler.table") as mock_table:
        mock_table.put_item.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}
        res = handler(event, fake_ctx)

    assert "option1" in res and "option2" in res and "option3" in res
    # Values can be empty if no good match, but keys must exist