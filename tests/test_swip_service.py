#!/usr/bin/env python3
import json
import os
import shutil
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch, MagicMock

import swip.service
from swip.service import (
    _env_int,
    _env_bool,
    _read_config_file,
    _load_config,
    Handler,
    main,
)


class SwipServiceHelperTests(unittest.TestCase):
    def test_env_int(self):
        with patch.dict(os.environ, {"TEST_INT": "42"}):
            self.assertEqual(_env_int("TEST_INT", 10), 42)
        with patch.dict(os.environ, {"TEST_INT": "invalid"}):
            self.assertEqual(_env_int("TEST_INT", 10), 10)
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(_env_int("TEST_INT", 10), 10)

    def test_env_bool(self):
        for true_val in ["1", "true", "TRUE", "yes", "YES", "on", "ON"]:
            with patch.dict(os.environ, {"TEST_BOOL": true_val}):
                self.assertTrue(_env_bool("TEST_BOOL", False))

        for false_val in ["0", "false", "no", "off", "other"]:
            with patch.dict(os.environ, {"TEST_BOOL": false_val}):
                self.assertFalse(_env_bool("TEST_BOOL", True))

        with patch.dict(os.environ, {}, clear=True):
            self.assertTrue(_env_bool("TEST_BOOL", True))
            self.assertFalse(_env_bool("TEST_BOOL", False))

    def test_read_config_file(self):
        self.assertEqual(_read_config_file(""), {})
        self.assertEqual(_read_config_file("/path/does/not/exist.json"), {})

        temp_dir = Path(tempfile.mkdtemp())
        try:
            # Test JSON config file
            json_file = temp_dir / "config.json"
            json_file.write_text(json.dumps({"server": {"port": 9100}}), encoding="utf-8")
            self.assertEqual(_read_config_file(str(json_file)), {"server": {"port": 9100}})

            # Test JSON file containing non-dict
            json_list_file = temp_dir / "list_config.json"
            json_list_file.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
            self.assertEqual(_read_config_file(str(json_list_file)), {})

            # Test YAML config file
            yaml_file = temp_dir / "config.yaml"
            yaml_file.write_text("server:\n  port: 9200\n", encoding="utf-8")
            self.assertEqual(_read_config_file(str(yaml_file)), {"server": {"port": 9200}})

            # Test YML config file empty
            yml_file = temp_dir / "config.yml"
            yml_file.write_text("", encoding="utf-8")
            self.assertEqual(_read_config_file(str(yml_file)), {})

            # Test unsupported extension
            txt_file = temp_dir / "config.txt"
            txt_file.write_text("server=9100", encoding="utf-8")
            self.assertEqual(_read_config_file(str(txt_file)), {})
        finally:
            shutil.rmtree(temp_dir)


class SwipServiceConfigAndHandlerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.orig_config = dict(swip.service.CONFIG)
        swip.service.CONFIG["state_dir"] = str(self.temp_dir)

    def tearDown(self):
        swip.service.CONFIG.clear()
        swip.service.CONFIG.update(self.orig_config)
        shutil.rmtree(self.temp_dir)

    def test_load_config_default(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch("swip.service._read_config_file", return_value={}):
                cfg = _load_config()
                self.assertEqual(cfg["host"], "0.0.0.0")
                self.assertEqual(cfg["port"], 9100)
                self.assertEqual(cfg["metrics_enabled"], True)
                self.assertEqual(cfg["metrics_port"], 9101)
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
                "SWIP_CONFIG_FILE": "dummy.json",
                "SWIP_SERVER_HOST": "10.0.0.1",
                "SWIP_SERVER_PORT": "12000",
                "SWIP_METRICS_ENABLED": "true",
                "SWIP_METRICS_PORT": "12001",
                "SWIP_PROFILING_ENABLED": "true",
                "SWIP_PROFILING_DEFAULT_DURATION_SECONDS": "5",
                "SWIP_STATE_DIR": "env_data",
            },
            clear=True,
        ):
            with patch("swip.service._read_config_file", return_value=file_cfg) as mock_read:
                cfg = _load_config()
                mock_read.assert_called_with("dummy.json")
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

    def test_handler_get_default_path(self):
        handler = self._create_handler("/other", "GET")
        handler.do_GET()
        self.assertEqual(handler.response_code, 200)
        data = json.loads(handler.wfile.getvalue().decode())
        self.assertEqual(data, {"status": "ok"})

    def test_handler_get_profiling_disabled(self):
        swip.service.CONFIG["profiling_enabled"] = False
        handler = self._create_handler("/debug/profile", "GET")
        handler.do_GET()
        self.assertEqual(handler.response_code, 404)
        data = json.loads(handler.wfile.getvalue().decode())
        self.assertEqual(data, {"error": "profiling disabled"})

    @patch("pyinstrument.Profiler")
    def test_handler_get_profiling_enabled(self, mock_profiler_class):
        swip.service.CONFIG["profiling_enabled"] = True
        swip.service.CONFIG["default_profile_duration_seconds"] = 0

        mock_profiler = MagicMock()
        mock_profiler.output_html.return_value = "<html>Dummy SWIP Profile</html>"
        mock_profiler_class.return_value = mock_profiler

        handler = self._create_handler("/debug/profile?duration=0", "GET")
        handler.do_GET()
        self.assertEqual(handler.response_code, 200)
        self.assertEqual(handler.response_headers["content-type"], "text/html; charset=utf-8")
        html_output = handler.wfile.getvalue().decode()
        self.assertEqual(html_output, "<html>Dummy SWIP Profile</html>")

        profiles_dir = self.temp_dir / "profiles"
        self.assertTrue(profiles_dir.exists())
        profile_files = list(profiles_dir.glob("swip-profile-*.html"))
        self.assertEqual(len(profile_files), 1)
        self.assertEqual(profile_files[0].read_text(), "<html>Dummy SWIP Profile</html>")

    @patch("pyinstrument.Profiler")
    def test_handler_get_profiling_invalid_duration_query(self, mock_profiler_class):
        swip.service.CONFIG["profiling_enabled"] = True
        swip.service.CONFIG["default_profile_duration_seconds"] = 0

        mock_profiler = MagicMock()
        mock_profiler.output_html.return_value = "<html>Fallback Profile</html>"
        mock_profiler_class.return_value = mock_profiler

        handler = self._create_handler("/debug/pprof?duration=not_a_number", "GET")
        handler.do_GET()
        self.assertEqual(handler.response_code, 200)
        html_output = handler.wfile.getvalue().decode()
        self.assertEqual(html_output, "<html>Fallback Profile</html>")

    @patch.dict("sys.modules", {"pyinstrument": None})
    def test_handler_get_profiling_no_pyinstrument(self):
        swip.service.CONFIG["profiling_enabled"] = True
        swip.service.CONFIG["default_profile_duration_seconds"] = 0

        handler = self._create_handler("/debug/profile", "GET")
        handler.do_GET()
        self.assertEqual(handler.response_code, 500)
        data = json.loads(handler.wfile.getvalue().decode())
        self.assertEqual(data, {"error": "pyinstrument not installed"})

    @patch("pyinstrument.Profiler")
    def test_handler_get_profiling_exception(self, mock_profiler_class):
        swip.service.CONFIG["profiling_enabled"] = True
        swip.service.CONFIG["default_profile_duration_seconds"] = 0

        mock_profiler_class.side_effect = RuntimeError("Profiling failed")

        handler = self._create_handler("/debug/profile", "GET")
        handler.do_GET()
        self.assertEqual(handler.response_code, 500)
        data = json.loads(handler.wfile.getvalue().decode())
        self.assertEqual(data, {"error": "Profiling failed"})

    def test_handler_post_valid_payload(self):
        payload = json.dumps({"value": 4.0}).encode("utf-8")
        handler = self._create_handler(
            "/", "POST", body=payload, headers={"Content-Length": str(len(payload))}
        )
        handler.do_POST()
        self.assertEqual(handler.response_code, 200)
        data = json.loads(handler.wfile.getvalue().decode())
        self.assertEqual(data, {"result": 6.0})

    def test_handler_post_default_value(self):
        payload = json.dumps({}).encode("utf-8")
        handler = self._create_handler(
            "/", "POST", body=payload, headers={"Content-Length": str(len(payload))}
        )
        handler.do_POST()
        self.assertEqual(handler.response_code, 200)
        data = json.loads(handler.wfile.getvalue().decode())
        self.assertEqual(data, {"result": 1.5})

    def test_handler_post_invalid_json(self):
        handler = self._create_handler(
            "/", "POST", body=b"invalid json", headers={"Content-Length": "12"}
        )
        handler.do_POST()
        self.assertEqual(handler.response_code, 400)
        data = json.loads(handler.wfile.getvalue().decode())
        self.assertEqual(data, {"error": "invalid json"})

    def test_handler_post_empty_body(self):
        handler = self._create_handler("/", "POST", body=b"", headers={})
        handler.do_POST()
        self.assertEqual(handler.response_code, 400)
        data = json.loads(handler.wfile.getvalue().decode())
        self.assertEqual(data, {"error": "invalid json"})

    @patch("swip.service.HTTPServer")
    @patch("swip.service.start_http_server")
    def test_main(self, mock_start_http_server, mock_http_server):
        mock_server_inst = MagicMock()
        mock_http_server.return_value = mock_server_inst

        swip.service.CONFIG["metrics_enabled"] = True
        swip.service.CONFIG["metrics_port"] = 9101
        swip.service.CONFIG["host"] = "0.0.0.0"
        swip.service.CONFIG["port"] = 9100

        main()

        mock_start_http_server.assert_called_once_with(9101)
        mock_http_server.assert_called_once_with(("0.0.0.0", 9100), Handler)
        mock_server_inst.serve_forever.assert_called_once()

    @patch("swip.service.HTTPServer")
    @patch("swip.service.start_http_server")
    def test_main_metrics_disabled(self, mock_start_http_server, mock_http_server):
        mock_server_inst = MagicMock()
        mock_http_server.return_value = mock_server_inst

        swip.service.CONFIG["metrics_enabled"] = False
        swip.service.CONFIG["host"] = "127.0.0.1"
        swip.service.CONFIG["port"] = 9100

        main()

        mock_start_http_server.assert_not_called()
        mock_http_server.assert_called_once_with(("127.0.0.1", 9100), Handler)
        mock_server_inst.serve_forever.assert_called_once()


if __name__ == "__main__":
    unittest.main()
