from unittest import TestCase

from lark import Lark

from services.transformer.simple_rule_engine_transformer import SimpleRuleEngineTransformer


class TestCustomDecisionRuleLark(TestCase):
    def test_rule_complex_decision(self):
        with open("./decision_rule.lark") as rule_grammar_file:
            rule_grammar = rule_grammar_file.read()

        parser = Lark(rule_grammar)

        custom_rule = """
            my_rule {
                when {
                    cibil_score between 650 and 750 and 
                    age > 35 and 
                    house_ownership in (owned, rented) and
                    (
                        total_overdue_amount == 0 or 
                        number_of_overdue_loans < 2 or
                        (
                            number_of_overdue_loans >= 2 and
                            big_shot == true
                        )
                    ) and
                    pet == dog
                }
                then true
                when {
                    cibil_score < 650
                }
                then false
            }
            """

        tree = parser.parse(custom_rule)
        print(tree.pretty())

        decision_rule = SimpleRuleEngineTransformer(tree).get_rule()

        # Evaluate the Decision Rule by passing data
        facts = dict(
            cibil_score=700,
            age=40,
            house_ownership="owned",
            total_overdue_amount=0,
            pet="dog"
        )
        assert decision_rule.execute(token_dict=facts) is True

        facts = dict(
            cibil_score=700,
            age=40,
            house_ownership="owned",
            total_overdue_amount=100,
            number_of_overdue_loans=1,
            pet="dog"
        )
        assert decision_rule.execute(token_dict=facts) is True

        facts = dict(
            cibil_score=700,
            age=40,
            house_ownership="owned",
            total_overdue_amount=100,
            number_of_overdue_loans=2,
            big_shot="true",
            pet="dog"
        )
        assert decision_rule.execute(token_dict=facts) is True

        facts = dict(
            cibil_score=600,
            age=40,
            house_ownership="owned",
            total_overdue_amount=100,
            number_of_overdue_loans=2,
            big_shot="false",
            pet="dog"
        )
        assert decision_rule.execute(token_dict=facts) is False
