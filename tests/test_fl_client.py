import unittest
from unittest.mock import patch

from fl.client import FLClient, load_client_from_env


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def request(self, method, url, timeout, **kwargs):
        self.calls.append({
            "method": method,
            "url": url,
            "timeout": timeout,
            "kwargs": kwargs,
        })
        if not self._responses:
            raise RuntimeError("no response queued")
        result = self._responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


class FLClientTests(unittest.TestCase):
    def test_retries_transient_failures_then_succeeds(self):
        session = FakeSession([
            RuntimeError("temporary network"),
            FakeResponse(200, {"round": 2, "global": 0.4}),
        ])
        sleep_calls = []

        client = FLClient(
            coord_url="http://coordinator:9000",
            max_retries=2,
            session=session,
            sleeper=lambda seconds: sleep_calls.append(seconds),
            jitter=lambda: 0.0,
            logger=lambda *args: None,
        )

        state = client.fetch_state()
        self.assertEqual(state["round"], 2)
        self.assertEqual(len(session.calls), 2)
        self.assertEqual(len(sleep_calls), 1)

    def test_does_not_retry_client_error(self):
        session = FakeSession([FakeResponse(400, {"error": "bad request"})])
        sleep_calls = []

        client = FLClient(
            coord_url="http://coordinator:9000",
            max_retries=3,
            session=session,
            sleeper=lambda seconds: sleep_calls.append(seconds),
            jitter=lambda: 0.0,
            logger=lambda *args: None,
        )

        with self.assertRaises(ValueError):
            client.fetch_state()

        self.assertEqual(len(session.calls), 1)
        self.assertEqual(sleep_calls, [])

    def test_run_once_posts_update_value(self):
        session = FakeSession([
            FakeResponse(200, {"round": 1, "global": 0.1}),
            FakeResponse(200, {"round": 2, "global": 0.2}),
        ])

        client = FLClient(
            coord_url="http://coordinator:9000",
            session=session,
            logger=lambda *args: None,
        )

        with patch("fl.client.random.random", return_value=0.25):
            result = client.run_once()

        self.assertEqual(result["round"], 2)
        self.assertEqual(session.calls[0]["method"], "GET")
        self.assertEqual(session.calls[1]["method"], "POST")
        self.assertEqual(session.calls[1]["kwargs"]["json"], {"value": 0.25})

    def test_load_client_from_env_overrides_values(self):
        with patch.dict(
            "os.environ",
            {
                "COORD_HOST": "http://localhost:1234",
                "FL_CLIENT_GET_TIMEOUT_SECONDS": "7",
                "FL_CLIENT_POST_TIMEOUT_SECONDS": "8",
                "FL_CLIENT_MAX_RETRIES": "5",
                "FL_CLIENT_BASE_BACKOFF_SECONDS": "0.2",
                "FL_CLIENT_MAX_BACKOFF_SECONDS": "2.5",
                "FL_CLIENT_VERBOSE": "false",
            },
            clear=False,
        ):
            client = load_client_from_env()

        self.assertEqual(client.coord_url, "http://localhost:1234")
        self.assertEqual(client.get_timeout, 7.0)
        self.assertEqual(client.post_timeout, 8.0)
        self.assertEqual(client.max_retries, 5)
        self.assertEqual(client.base_backoff_seconds, 0.2)
        self.assertEqual(client.max_backoff_seconds, 2.5)


if __name__ == "__main__":
    unittest.main()
