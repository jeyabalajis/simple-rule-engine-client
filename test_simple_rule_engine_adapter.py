from unittest import TestCase

from services.adapter.simple_rule_engine_adapter import SimpleRuleEngineAdapter
from services.util.json_file_util import JsonFileUtil


class TestSimpleRuleEngineAdapter(TestCase):
    def test_rule_simple_decision(self):
        json_file_util = JsonFileUtil(file_name_with_path="./examples/simple_decision.json")
        decision_rule_dict = json_file_util.read_file()

        rule_engine_adapter = SimpleRuleEngineAdapter(rule_dict=decision_rule_dict)
        decision_rule = rule_engine_adapter.get_rule()

        assert type(decision_rule).__name__ == "RuleDecision"

        fact = dict(cibil_score=700, business_ownership="Owned by Self")
        assert decision_rule.execute(token_dict=fact) == "GO"

    def test_rule_simple_decision_when_any(self):
        json_file_util = JsonFileUtil(file_name_with_path="./examples/simple_decision_when_any.json")
        decision_rule_dict = json_file_util.read_file()

        rule_engine_adapter = SimpleRuleEngineAdapter(rule_dict=decision_rule_dict)
        decision_rule = rule_engine_adapter.get_rule()

        assert type(decision_rule).__name__ == "RuleDecision"

        fact = dict(age=35, pet="parrot")
        assert decision_rule.execute(token_dict=fact) == "GO"

        fact = dict(age=20, pet="dog")
        assert decision_rule.execute(token_dict=fact) != "GO"

    def test_rule_simple_score(self):
        json_file_util = JsonFileUtil(file_name_with_path="./examples/simple_score.json")
        score_rule_dict = json_file_util.read_file()

        rule_engine_adapter = SimpleRuleEngineAdapter(rule_dict=score_rule_dict)
        score_rule = rule_engine_adapter.get_rule()

        assert type(score_rule).__name__ == "RuleScore"

        fact = dict(age=40, pet="dog", domicile="TN")
        assert score_rule.execute(token_dict=fact) == 5.0

        fact = dict(age=40, pet="dog", domicile="KA")
        assert score_rule.execute(token_dict=fact) == 7.5
