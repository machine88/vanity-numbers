# lambda/vanity/tests/test_handler_connect.py
from unittest.mock import patch, MagicMock
from app.handler import handler

def test_handler_with_connect_event_shape():
    event = {
        "Details": {
            "ContactData": {
                "ContactId": "abc-123",
                "InstanceId": "inst-xyz",
                "CustomerEndpoint": {"Address": "+13035551212"},
            }
        }
    }
    fake_ctx = MagicMock()

    # Patch the DynamoDB table object referenced inside app.handler
    with patch("app.handler.table") as mock_table:
        mock_table.put_item.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}
        res = handler(event, fake_ctx)

    assert {"option1", "option2", "option3"}.issubset(res.keys())