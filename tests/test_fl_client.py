import unittest
from unittest.mock import patch, MagicMock
import sys
import importlib
import urllib.request
import urllib.error

from fl.client import FLClient, load_client_from_env, _UrllibSession


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

    def test_session_fallback_when_requests_missing(self):
        import fl.client
        with patch.dict(sys.modules, {"requests": None}):
            importlib.reload(fl.client)
            client = fl.client.FLClient(coord_url="http://coordinator:9000")
            self.assertEqual(client.session.__class__.__name__, "_UrllibSession")
        # clean up by restoring state
        importlib.reload(fl.client)

    def test_session_creation_when_requests_present(self):
        import fl.client
        mock_requests = MagicMock()
        mock_session_instance = MagicMock()
        mock_requests.Session.return_value = mock_session_instance

        with patch.dict(sys.modules, {"requests": mock_requests}):
            importlib.reload(fl.client)
            client = fl.client.FLClient(coord_url="http://coordinator:9000")
            self.assertEqual(client.session, mock_session_instance)
            mock_requests.Session.assert_called_once()
        # clean up by restoring state
        importlib.reload(fl.client)

    def test_urllib_session_success_dict(self):
        session = _UrllibSession()
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"round": 3}'
        mock_response.__enter__.return_value = mock_response

        with patch("urllib.request.urlopen", return_value=mock_response) as mock_urlopen:
            res = session.request("GET", "http://coordinator", timeout=5.0)
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json(), {"round": 3})
            mock_urlopen.assert_called_once()
            req = mock_urlopen.call_args[0][0]
            self.assertEqual(req.full_url, "http://coordinator")
            self.assertEqual(req.get_method(), "GET")

    def test_urllib_session_success_non_dict(self):
        session = _UrllibSession()
        mock_response = MagicMock()
        mock_response.status = 201
        mock_response.read.return_value = b'42'
        mock_response.__enter__.return_value = mock_response

        with patch("urllib.request.urlopen", return_value=mock_response) as mock_urlopen:
            res = session.request("POST", "http://coordinator", timeout=5.0, json={"value": 42})
            self.assertEqual(res.status_code, 201)
            self.assertEqual(res.json(), {"value": 42})
            req = mock_urlopen.call_args[0][0]
            self.assertEqual(req.get_method(), "POST")
            self.assertEqual(req.data, b'{"value": 42}')
            self.assertTrue(any(k.lower() == "content-type" for k in req.headers))

    def test_urllib_session_http_error_dict(self):
        session = _UrllibSession()
        fp = MagicMock()
        fp.read.return_value = b'{"error": "invalid parameter"}'
        err = urllib.error.HTTPError(
            url="http://coordinator",
            code=400,
            msg="Bad Request",
            hdrs={},
            fp=fp
        )

        with patch("urllib.request.urlopen", side_effect=err):
            res = session.request("GET", "http://coordinator", timeout=5.0)
            self.assertEqual(res.status_code, 400)
            self.assertEqual(res.json(), {"error": "invalid parameter"})

    def test_urllib_session_http_error_non_dict_json(self):
        session = _UrllibSession()
        fp = MagicMock()
        fp.read.return_value = b'"bad error"'
        err = urllib.error.HTTPError(
            url="http://coordinator",
            code=403,
            msg="Forbidden",
            hdrs={},
            fp=fp
        )

        with patch("urllib.request.urlopen", side_effect=err):
            res = session.request("GET", "http://coordinator", timeout=5.0)
            self.assertEqual(res.status_code, 403)
            self.assertEqual(res.json(), {"value": "bad error"})

    def test_urllib_session_http_error_invalid_json(self):
        session = _UrllibSession()
        fp = MagicMock()
        fp.read.return_value = b'not json'
        err = urllib.error.HTTPError(
            url="http://coordinator",
            code=500,
            msg="Internal Error",
            hdrs={},
            fp=fp
        )

        with patch("urllib.request.urlopen", side_effect=err):
            res = session.request("GET", "http://coordinator", timeout=5.0)
            self.assertEqual(res.status_code, 500)
            self.assertEqual(res.json(), {"error": "not json"})

    def test_urllib_session_http_error_empty_fp(self):
        session = _UrllibSession()
        err = urllib.error.HTTPError(
            url="http://coordinator",
            code=502,
            msg="Bad Gateway",
            hdrs={},
            fp=None
        )

        with patch("urllib.request.urlopen", side_effect=err):
            res = session.request("GET", "http://coordinator", timeout=5.0)
            self.assertEqual(res.status_code, 502)
            self.assertEqual(res.json(), {})


if __name__ == "__main__":
    unittest.main()
