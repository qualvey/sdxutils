import pytest
from unittest.mock import Mock
from datetime import date
from douyin.main import fetch_douyin_data

def test_fetch_douyin_data_success():
    mock_session = Mock()
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {'data': 'ok'}

    mock_session.post.return_value = mock_response

    test_date = date(2024, 5, 20)
    url = "http://test.url/api"
    headers = {"Authorization": "Bearer token"}
    cookies = {"sessionid": "123"}

    result = fetch_douyin_data(test_date, mock_session, url, headers, cookies)

    assert result == {'data': 'ok'}
    mock_session.post.assert_called_once()

def test_fetch_douyin_data_failure_retry():
    mock_session = Mock()
    mock_session.post.side_effect = Exception("network error")

    test_date = date(2024, 5, 20)
    url = "http://test.url/api"
    headers = {"Authorization": "Bearer token"}
    cookies = {"sessionid": "123"}

    result = fetch_douyin_data(test_date, mock_session, url, headers, cookies, max_retries=3, delay=0)

    assert result is None
    assert mock_session.post.call_count == 3
