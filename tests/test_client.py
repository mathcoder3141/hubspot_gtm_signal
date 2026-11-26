from unittest.mock import Mock, patch
from hubspot.client import HubSpotClient
import requests
import pytest

def test_request_returns_json_on_success():
    client = HubSpotClient.__new__(HubSpotClient)
    client.session = Mock()

    response = Mock()
    response.ok = True
    response.json.return_value = {"results": [{"id": "123"}]}

    client.session.request.return_value = response

    result = client.request("GET", "/crm/objects/companies")

    assert result == {"results": [{"id": "123"}]}
    client.session.request.assert_called_once()

def test_request_raises_non_retryable_error():
    client = HubSpotClient.__new__(HubSpotClient)
    client.session = Mock()

    response = Mock()
    response.ok = False
    response.status_code = 400
    response.raise_for_status.side_effect = requests.HTTPError("Bad Request")

    client.session.request.return_value = response

    with pytest.raises(requests.HTTPError, match="Bad Request"):
        client.request("GET", "/crm/objects/companies")

    client.session.request.assert_called_once()

def test_request_retries_on_server_error():
    client = HubSpotClient.__new__(HubSpotClient)
    client.session = Mock()

    failed_response = Mock()
    failed_response.ok = False
    failed_response.status_code = 500

    successful_response = Mock()
    successful_response.ok = True
    successful_response.json.return_value = {"success": True}

    client.session.request.side_effect = [
        failed_response,
        failed_response,
        successful_response,
    ]

    with patch("hubspot.client.time.sleep"):
        result = client.request("GET", "/test")

    assert result == {"success": True}
    assert client.session.request.call_count == 3

def test_request_uses_retry_after_for_rate_limit():
    client = HubSpotClient.__new__(HubSpotClient)
    client.session = Mock()

    rate_limited_response = Mock()
    rate_limited_response.ok = False
    rate_limited_response.status_code = 429
    rate_limited_response.headers = {"Retry-After": "10"}

    successful_response = Mock()
    successful_response.ok = True
    successful_response.json.return_value = {"success": True}

    client.session.request.side_effect = [
        rate_limited_response,
        successful_response,
    ]

    with patch("hubspot.client.time.sleep") as mock_sleep:
        result = client.request("GET", "/test")

    assert result == {"success": True}
    mock_sleep.assert_called_once_with(10)

def test_request_stops_after_max_retries():
    client = HubSpotClient.__new__(HubSpotClient)
    client.session = Mock()

    response = Mock()
    response.ok = False
    response.status_code = 503
    response.raise_for_status.side_effect = requests.HTTPError('Service Unavailable')

    client.session.request.return_value = response

    with patch("hubspot.client.time.sleep"):
        with pytest.raises(requests.HTTPError, match='Service Unavailable'):
            client.request("GET", "/test")

    assert client.session.request.call_count == 3