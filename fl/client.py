#!/usr/bin/env python3
import sys
from pathlib import Path

# Add the parent directory of fl to sys.path to enable absolute imports like from fl.common import ...
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import os
import time
import random
import urllib.error
import urllib.request
from typing import Any, Callable, Dict, Optional

from fl.common import env_int, env_float, env_bool, read_config_file


class FLClient:
    def __init__(
        self,
        coord_url: str,
        get_timeout: float = 5.0,
        post_timeout: float = 5.0,
        max_retries: int = 3,
        base_backoff_seconds: float = 0.5,
        max_backoff_seconds: float = 5.0,
        session: Optional[Any] = None,
        sleeper: Callable[[float], None] = time.sleep,
        jitter: Callable[[], float] = random.random,
        logger: Callable[..., None] = print,
    ):
        self.coord_url = coord_url.rstrip("/")
        self.get_timeout = get_timeout
        self.post_timeout = post_timeout
        self.max_retries = max(0, max_retries)
        self.base_backoff_seconds = max(0.0, base_backoff_seconds)
        self.max_backoff_seconds = max(0.0, max_backoff_seconds)
        self.sleeper = sleeper
        self.jitter = jitter
        self.logger = logger

        if session is None:
            try:
                import requests

                session = requests.Session()
            except ModuleNotFoundError:
                session = _UrllibSession()
        self.session = session

    def _sleep_for_attempt(self, attempt: int) -> None:
        if attempt <= 0:
            return
        delay = min(
            self.max_backoff_seconds,
            self.base_backoff_seconds * (2 ** (attempt - 1)),
        )
        # Add jitter to avoid synchronized retries when many devices reconnect.
        delay = delay * (0.5 + self.jitter())
        self.sleeper(delay)

    def _request_with_retry(self, method: str, timeout: float, **kwargs: Any) -> Any:
        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            if attempt > 0:
                self._sleep_for_attempt(attempt)

            try:
                response = self.session.request(
                    method=method,
                    url=self.coord_url,
                    timeout=timeout,
                    **kwargs,
                )
                status_code = int(getattr(response, "status_code", 200))
                if status_code >= 500:
                    raise RuntimeError(f"server error: {status_code}")
                if status_code >= 400:
                    raise ValueError(f"client error: {status_code}")
                return response
            except ValueError:
                raise
            except Exception as error:
                last_error = error
                if attempt == self.max_retries:
                    break

        assert last_error is not None
        raise RuntimeError(f"request failed after retries: {last_error}") from last_error

    def fetch_state(self) -> Dict[str, Any]:
        response = self._request_with_retry("GET", timeout=self.get_timeout)
        try:
            return response.json()
        except Exception as error:
            raise RuntimeError(f"invalid state response: {error}") from error

    def submit_update(self, value: float) -> Dict[str, Any]:
        response = self._request_with_retry(
            "POST",
            timeout=self.post_timeout,
            json={"value": value},
        )
        try:
            return response.json()
        except Exception as error:
            raise RuntimeError(f"invalid update response: {error}") from error

    def run_once(self) -> Dict[str, Any]:
        state = self.fetch_state()
        value = random.random()
        self.logger("Submitting update", value, "current round", state.get("round"))
        return self.submit_update(value)

    def run_forever(self, interval_seconds: float = 5.0) -> None:
        while True:
            try:
                self.run_once()
            except Exception as error:
                self.logger("error", error)
            self.sleeper(interval_seconds)


class _SimpleResponse:
    def __init__(self, status_code: int, payload: Dict[str, Any]):
        self.status_code = status_code
        self._payload = payload

    def json(self) -> Dict[str, Any]:
        return self._payload


class _UrllibSession:
    def request(self, method: str, url: str, timeout: float, **kwargs: Any) -> _SimpleResponse:
        payload = kwargs.get("json")
        body = None
        headers = {}
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = urllib.request.Request(url=url, data=body, method=method, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                status_code = int(getattr(response, "status", 200))
                raw = response.read().decode("utf-8")
                parsed = json.loads(raw) if raw else {}
                if not isinstance(parsed, dict):
                    parsed = {"value": parsed}
                return _SimpleResponse(status_code, parsed)
        except urllib.error.HTTPError as error:
            raw = error.read().decode("utf-8") if error.fp is not None else ""
            parsed = {}
            if raw:
                try:
                    decoded = json.loads(raw)
                    if isinstance(decoded, dict):
                        parsed = decoded
                    else:
                        parsed = {"value": decoded}
                except Exception:
                    parsed = {"error": raw}
            return _SimpleResponse(error.code, parsed)


def load_client_from_env() -> FLClient:
    cfg = read_config_file(os.environ.get("FL_CLIENT_CONFIG_FILE", "").strip())
    coord = os.environ.get("COORD_HOST", cfg.get("coord_url", "http://fl-coordinator:9000"))

    get_timeout = env_float("FL_CLIENT_GET_TIMEOUT_SECONDS", float(cfg.get("get_timeout", 5.0)))
    post_timeout = env_float("FL_CLIENT_POST_TIMEOUT_SECONDS", float(cfg.get("post_timeout", 5.0)))
    retries = env_int("FL_CLIENT_MAX_RETRIES", int(cfg.get("max_retries", 3)))
    backoff_base = env_float("FL_CLIENT_BASE_BACKOFF_SECONDS", float(cfg.get("base_backoff_seconds", 0.5)))
    backoff_max = env_float("FL_CLIENT_MAX_BACKOFF_SECONDS", float(cfg.get("max_backoff_seconds", 5.0)))

    if env_bool("FL_CLIENT_VERBOSE", True):
        print(
            "FL client config",
            {
                "coord_url": coord,
                "get_timeout": get_timeout,
                "post_timeout": post_timeout,
                "max_retries": retries,
            },
        )

    return FLClient(
        coord_url=coord,
        get_timeout=get_timeout,
        post_timeout=post_timeout,
        max_retries=retries,
        base_backoff_seconds=backoff_base,
        max_backoff_seconds=backoff_max,
    )

def main():
    client = load_client_from_env()
    interval = env_float("FL_CLIENT_POLL_INTERVAL_SECONDS", 5.0)
    client.run_forever(interval_seconds=interval)

if __name__ == '__main__':
    main()
