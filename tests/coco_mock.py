from mockito import when, mock, unstub
import json
import requests

BASE_URL = "https://meetiqm.com/api/"


def mock_backend():
    success_submit_response = mock({'status_code': 201, 'text': json.dumps({"id": 14})})
    when(requests).post(f"{BASE_URL}/circuit/run", ...).thenReturn(success_submit_response)

    running_response = mock({'status_code': 200, 'text': json.dumps({"status": "pending"})})
    success_get_response = mock({'status_code': 200, 'text': json.dumps(
        {"status": "ready", "measurements": {"result": [[1, 0, 1, 1], [1, 0, 0, 1], [1, 0, 1, 1], [1, 0, 1, 1]]}})})
    no_run_response = mock({'status_code': 404, 'text': "Run not found"})

    when(requests).get(f"{BASE_URL}/circuit/run/14", ...).thenReturn(running_response).thenReturn(success_get_response)
    when(requests).get(f"{BASE_URL}/circuit/run/13", ...).thenReturn(no_run_response)
