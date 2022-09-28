from unittest import TestCase

from services.adapter.simple_rule_engine_adapter import SimpleRuleEngineAdapter
from services.util.json_file_util import JsonFileUtil


class TestSimpleRuleEngineAdapter(TestCase):
    def test_get_rule(self):
        json_file_util = JsonFileUtil(file_name_with_path="./examples/simple_decision.json")
        decision_dict = json_file_util.read_file()

        rule_engine_adapter = SimpleRuleEngineAdapter(rule_dict=decision_dict)
        decision_rule = rule_engine_adapter.get_rule()

        assert type(decision_rule).__name__ == "RuleDecision"

        fact = dict(cibil_score=700, business_ownership="Owned by Self")
        assert decision_rule.execute(token_dict=fact) == "GO"

