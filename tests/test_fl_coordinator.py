import unittest
import os
import json
import tempfile
import shutil
import time
from io import BytesIO
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import coordinator
import fl.coordinator
from fl.coordinator import (
    _env_int,
    _env_bool,
    _read_config_file,
    _load_config,
    Handler,
)


class FLCoordinatorHelperTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)

    def test_env_int(self):
        # Missing env var
        if "TEST_INT" in os.environ:
            del os.environ["TEST_INT"]
        self.assertEqual(_env_int("TEST_INT", 42), 42)

        # Valid int
        os.environ["TEST_INT"] = "100"
        self.assertEqual(_env_int("TEST_INT", 42), 100)

        # Invalid int
        os.environ["TEST_INT"] = "not_an_int"
        self.assertEqual(_env_int("TEST_INT", 42), 42)

    def test_env_bool(self):
        # Missing env var
        if "TEST_BOOL" in os.environ:
            del os.environ["TEST_BOOL"]
        self.assertEqual(_env_bool("TEST_BOOL", False), False)
        self.assertEqual(_env_bool("TEST_BOOL", True), True)

        # Truthy values
        for val in ["1", "true", "yes", "on", " TRUE ", "Yes"]:
            os.environ["TEST_BOOL"] = val
            self.assertTrue(_env_bool("TEST_BOOL", False))

        # Falsy values
        for val in ["0", "false", "no", "off", "invalid", ""]:
            os.environ["TEST_BOOL"] = val
            self.assertFalse(_env_bool("TEST_BOOL", True))

    def test_read_config_file(self):
        # Empty/None path
        self.assertEqual(_read_config_file(""), {})

        # Non-existent path
        self.assertEqual(_read_config_file("non_existent_file.json"), {})

        # Valid JSON file
        json_path = Path(self.temp_dir) / "config.json"
        config_data = {"server": {"port": 1234}}
        json_path.write_text(json.dumps(config_data), encoding="utf-8")
        self.assertEqual(_read_config_file(str(json_path)), config_data)


class FLCoordinatorConfigAndHandlerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_state_dir = Path(self.temp_dir) / "run_data"
        self.temp_state_dir.mkdir(
            parents=True, exist_ok=True
        )  # Ensure state directory exists!
        self.temp_state_file = self.temp_state_dir / "rounds.json"

        # Patch the global state file location inside fl.coordinator
        self.state_patcher = patch("fl.coordinator.STATE", new=self.temp_state_file)
        self.mock_state = self.state_patcher.start()

        # Force re-initialization of coordinator state cache so it uses the patched STATE path and is isolated from other tests
        fl.coordinator._init_state()

        # Save original config to restore later
        self.original_config = fl.coordinator.CONFIG.copy()

        self.addCleanup(self.state_patcher.stop)
        self.addCleanup(shutil.rmtree, self.temp_dir)
        self.addCleanup(self._restore_config)

    def _restore_config(self):
        fl.coordinator.CONFIG.clear()
        fl.coordinator.CONFIG.update(self.original_config)

    def test_load_config_default(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch("fl.coordinator._read_config_file", return_value={}):
                cfg = _load_config()
                self.assertEqual(cfg["host"], "0.0.0.0")
                self.assertEqual(cfg["port"], 9000)
                self.assertEqual(cfg["metrics_enabled"], True)
                self.assertEqual(cfg["metrics_port"], 9001)
                self.assertEqual(cfg["profiling_enabled"], True)
                self.assertEqual(cfg["default_profile_duration_seconds"], 2)
                self.assertEqual(cfg["state_dir"], "run_data")

    def test_load_config_with_file_and_env_overrides(self):
        file_cfg = {
            "server": {"host": "127.0.0.1", "port": 8000},
            "metrics": {"enabled": False, "port": 8001},
            "profiling": {"enabled": False, "default_duration_seconds": 10},
            "storage": {"state_dir": "custom_data"},
        }
        with patch.dict(
            os.environ,
            {
                "FL_CONFIG_FILE": "dummy.json",
                "FL_SERVER_HOST": "10.0.0.1",
                "FL_SERVER_PORT": "12000",
                "FL_METRICS_ENABLED": "true",
                "FL_METRICS_PORT": "12001",
                "FL_PROFILING_ENABLED": "true",
                "FL_PROFILING_DEFAULT_DURATION_SECONDS": "5",
                "FL_STATE_DIR": "env_data",
            },
            clear=True,
        ):
            with patch(
                "fl.coordinator._read_config_file", return_value=file_cfg
            ) as mock_read:
                cfg = _load_config()
                mock_read.assert_called_with("dummy.json")
                # Environment variables override file config
                self.assertEqual(cfg["host"], "10.0.0.1")
                self.assertEqual(cfg["port"], 12000)
                self.assertEqual(cfg["metrics_enabled"], True)
                self.assertEqual(cfg["metrics_port"], 12001)
                self.assertEqual(cfg["profiling_enabled"], True)
                self.assertEqual(cfg["default_profile_duration_seconds"], 5)
                self.assertEqual(cfg["state_dir"], "env_data")

    def _create_handler(self, path, method="GET", body=b"", headers=None):
        if headers is None:
            headers = {}

        # Subclass Handler to bypass BaseHTTPRequestHandler initialization
        class TestableHandler(Handler):
            def __init__(self):
                self.rfile = BytesIO(body)
                self.wfile = BytesIO()
                self.headers = headers
                self.path = path
                self.command = method
                self.response_code = None
                self.response_headers = {}

            def send_response(self, code, message=None):
                self.response_code = code

            def send_header(self, keyword, value):
                self.response_headers[keyword.lower()] = value

            def end_headers(self):
                pass

            def log_message(self, format, *args):
                pass

        return TestableHandler()

    def test_handler_get_healthz(self):
        handler = self._create_handler("/healthz", "GET")
        handler.do_GET()
        self.assertEqual(handler.response_code, 200)
        self.assertEqual(handler.response_headers["content-type"], "application/json")
        data = json.loads(handler.wfile.getvalue().decode())
        self.assertEqual(data, {"status": "ok"})

    def test_handler_get_ready(self):
        handler = self._create_handler("/ready", "GET")
        handler.do_GET()
        self.assertEqual(handler.response_code, 200)
        data = json.loads(handler.wfile.getvalue().decode())
        self.assertEqual(data, {"ready": True})

    def test_handler_get_root_no_state_file(self):
        # State file doesn't exist yet
        if self.temp_state_file.exists():
            self.temp_state_file.unlink()
        handler = self._create_handler("/", "GET")
        handler.do_GET()
        self.assertEqual(handler.response_code, 200)
        data = json.loads(handler.wfile.getvalue().decode())
        self.assertEqual(data, {"round": 0, "global": 0.0})

    def test_handler_get_root_with_existing_state_file(self):
        state_data = {"round": 3, "global": 0.75}
        self.temp_state_file.write_text(json.dumps(state_data), encoding="utf-8")

        # Reload cache because we bypassed memory by writing directly to disk
        fl.coordinator._init_state()

        handler = self._create_handler("/", "GET")
        handler.do_GET()
        self.assertEqual(handler.response_code, 200)
        data = json.loads(handler.wfile.getvalue().decode())
        self.assertEqual(data, state_data)

    def test_handler_get_profiling_disabled(self):
        fl.coordinator.CONFIG["profiling_enabled"] = False
        handler = self._create_handler("/debug/profile", "GET")
        handler.do_GET()
        self.assertEqual(handler.response_code, 404)
        data = json.loads(handler.wfile.getvalue().decode())
        self.assertEqual(data, {"error": "profiling disabled"})

    @patch("pyinstrument.Profiler")
    def test_handler_get_profiling_enabled(self, mock_profiler_class):
        fl.coordinator.CONFIG["profiling_enabled"] = True
        fl.coordinator.CONFIG["default_profile_duration_seconds"] = (
            0  # Avoid actual sleeping/looping
        )

        mock_profiler = MagicMock()
        mock_profiler.output_html.return_value = "<html>Dummy Profile</html>"
        mock_profiler_class.return_value = mock_profiler

        handler = self._create_handler("/debug/profile?duration=1", "GET")
        handler.do_GET()
        self.assertEqual(handler.response_code, 200)
        self.assertEqual(
            handler.response_headers["content-type"], "text/html; charset=utf-8"
        )
        html_output = handler.wfile.getvalue().decode()
        self.assertEqual(html_output, "<html>Dummy Profile</html>")

        # Confirm file was created in profiles directory
        profiles_dir = self.temp_state_dir / "profiles"
        self.assertTrue(profiles_dir.exists())
        profile_files = list(profiles_dir.glob("fl-profile-*.html"))
        self.assertEqual(len(profile_files), 1)
        self.assertEqual(profile_files[0].read_text(), "<html>Dummy Profile</html>")

    @patch("pyinstrument.Profiler")
    def test_handler_get_profiling_invalid_duration_fallback(self, mock_profiler_class):
        fl.coordinator.CONFIG["profiling_enabled"] = True
        fl.coordinator.CONFIG["default_profile_duration_seconds"] = 0

        mock_profiler = MagicMock()
        mock_profiler.output_html.return_value = "<html>Fallback Profile</html>"
        mock_profiler_class.return_value = mock_profiler

        # Passer duration=invalid will cause an exception in parsing, which is caught and falls back to default.
        handler = self._create_handler("/debug/profile?duration=invalid_int", "GET")
        handler.do_GET()
        self.assertEqual(handler.response_code, 200)
        html_output = handler.wfile.getvalue().decode()
        self.assertEqual(html_output, "<html>Fallback Profile</html>")

    @patch("pyinstrument.Profiler")
    def test_handler_get_profiling_exception(self, mock_profiler_class):
        fl.coordinator.CONFIG["profiling_enabled"] = True
        fl.coordinator.CONFIG["default_profile_duration_seconds"] = 0

        # Make pyinstrument raise an exception during profiling
        mock_profiler_class.side_effect = RuntimeError("Profiling failed")

        handler = self._create_handler("/debug/profile?duration=1", "GET")
        handler.do_GET()
        self.assertEqual(handler.response_code, 500)
        data = json.loads(handler.wfile.getvalue().decode())
        self.assertEqual(data, {"error": "Profiling failed"})

    def test_handler_post_invalid_json(self):
        handler = self._create_handler(
            "/", "POST", body=b"not a valid json", headers={"Content-Length": "16"}
        )
        handler.do_POST()
        self.assertEqual(handler.response_code, 400)
        data = json.loads(handler.wfile.getvalue().decode())
        self.assertEqual(data, {"error": "invalid json"})

    def test_handler_post_single_update(self):
        if self.temp_state_file.exists():
            self.temp_state_file.unlink()

        # First post request (value = 0.5)
        payload = json.dumps({"value": 0.5}).encode()
        handler = self._create_handler(
            "/", "POST", body=payload, headers={"Content-Length": str(len(payload))}
        )
        handler.do_POST()

        self.assertEqual(handler.response_code, 200)
        data = json.loads(handler.wfile.getvalue().decode())
        # Since it's only 1 update, round hasn't advanced and aggregation hasn't run yet.
        self.assertEqual(data["round"], 0)
        self.assertEqual(data["updates"], [0.5])

        # Wait for async file writing to complete before assertion
        fl.coordinator._flush_state()

        # Confirm written to state file
        file_data = json.loads(self.temp_state_file.read_text())
        self.assertEqual(file_data["round"], 0)
        self.assertEqual(file_data["updates"], [0.5])

    def test_handler_post_aggregation(self):
        if self.temp_state_file.exists():
            self.temp_state_file.unlink()

        # Send first update (value = 0.2)
        payload1 = json.dumps({"value": 0.2}).encode()
        handler1 = self._create_handler(
            "/", "POST", body=payload1, headers={"Content-Length": str(len(payload1))}
        )
        handler1.do_POST()

        # Send second update (value = 0.8)
        payload2 = json.dumps({"value": 0.8}).encode()
        handler2 = self._create_handler(
            "/", "POST", body=payload2, headers={"Content-Length": str(len(payload2))}
        )
        handler2.do_POST()

        self.assertEqual(handler2.response_code, 200)
        data = json.loads(handler2.wfile.getvalue().decode())
        # Round advanced from 0 to 1, global value aggregated (0.2 + 0.8) / 2 = 0.5
        self.assertEqual(data["round"], 1)
        self.assertEqual(data["global"], 0.5)
        self.assertEqual(data.get("updates", []), [])

        # Wait for async file writing to complete before assertion
        fl.coordinator._flush_state()

        # Confirm state file has updated aggregation
        file_data = json.loads(self.temp_state_file.read_text())
        self.assertEqual(file_data["round"], 1)
        self.assertEqual(file_data["global"], 0.5)
        self.assertEqual(file_data.get("updates", []), [])


if __name__ == "__main__":
    unittest.main()
