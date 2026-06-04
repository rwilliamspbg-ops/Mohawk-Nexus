import json
import pathlib
import unittest

from mohawk_sdk.logic import fl_apply_update, swip_scale


class ConformanceTests(unittest.TestCase):
    def test_conformance_cases(self):
        fixture_path = (
            pathlib.Path(__file__).resolve().parents[2]
            / "fixtures"
            / "conformance"
            / "cases.json"
        )
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))

        for case in payload["cases"]:
            name = case["name"]
            kind = case["kind"]
            expected = case["expected"]

            with self.subTest(name=name):
                if kind == "swip_scale":
                    result = {"result": swip_scale(case["input"]["value"])}
                elif kind == "fl_apply_update":
                    result = fl_apply_update(case["input"]["state"], case["input"]["value"])
                else:
                    self.fail(f"unknown case kind: {kind}")

                self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
