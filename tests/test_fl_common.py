import os
import unittest
from unittest.mock import patch
from fl import common


class FLCommonTests(unittest.TestCase):
    def test_env_int(self):
        with patch.dict(os.environ, {"TEST_INT": "42"}):
            self.assertEqual(common.env_int("TEST_INT", 10), 42)
        with patch.dict(os.environ, {"TEST_INT": "invalid"}):
            self.assertEqual(common.env_int("TEST_INT", 10), 10)
        self.assertEqual(common.env_int("TEST_INT_MISSING", 10), 10)

    def test_env_bool(self):
        for val in ["1", "true", "yes", "on", "  True  "]:
            with patch.dict(os.environ, {"TEST_BOOL": val}):
                self.assertTrue(common.env_bool("TEST_BOOL", False))
        for val in ["0", "false", "no", "off", "invalid"]:
            with patch.dict(os.environ, {"TEST_BOOL": val}):
                self.assertFalse(common.env_bool("TEST_BOOL", True))
        self.assertTrue(common.env_bool("TEST_BOOL_MISSING", True))

    def test_env_float(self):
        with patch.dict(os.environ, {"TEST_FLOAT": "3.14"}):
            self.assertEqual(common.env_float("TEST_FLOAT", 1.0), 3.14)
        with patch.dict(os.environ, {"TEST_FLOAT": "invalid"}):
            self.assertEqual(common.env_float("TEST_FLOAT", 1.0), 1.0)
        self.assertEqual(common.env_float("TEST_FLOAT_MISSING", 1.0), 1.0)


if __name__ == "__main__":
    unittest.main()
