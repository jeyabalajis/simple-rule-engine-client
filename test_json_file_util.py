from unittest import TestCase
from services.util.json_file_util import JsonFileUtil


class TestJsonFileUtil(TestCase):
    def test_read_file(self):
        json_file_util = JsonFileUtil(file_name_with_path="./examples/simple_decision.json")
        decision_dict = json_file_util.read_file()

        assert type(decision_dict).__name__ == "dict"

        assert (
                "RuleDecision" in decision_dict and
                "RuleRows" in decision_dict.get("RuleDecision")
        )
