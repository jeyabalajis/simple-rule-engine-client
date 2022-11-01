import pytest
from lark import Lark

from services.adapter.simple_rule_engine_lark_tree_adapter import SimpleRuleEngineLarkTreeAdapter


@pytest.fixture
def decision_rule_grammar():
    with open("./decision_rule.lark") as rule_grammar_file:
        rule_grammar = rule_grammar_file.read()

    return rule_grammar


def test_rule_simple_decision(decision_rule_grammar):
    parser = Lark(decision_rule_grammar)

    custom_rule = """
        my_rule {
            when {
                cibil_score > 650 and
                age > 35 and
                house_ownership in (owned, rented) and
                (pet == dog or pet == parrot)
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

    decision_rule = SimpleRuleEngineLarkTreeAdapter(tree).get_rule()

    facts = dict(
        cibil_score=700,
        age=40,
        house_ownership="owned",
        pet="parrot"
    )

    assert decision_rule.execute(facts) is True

    facts = dict(
        cibil_score=700,
        age=40,
        house_ownership="owned",
        pet="pig"
    )

    assert decision_rule.execute(facts) is not True

    facts = dict(
        cibil_score=500,
        age=40,
        house_ownership="owned",
        pet="dog"
    )

    assert decision_rule.execute(facts) is not True


def test_rule_complex_decision(decision_rule_grammar):
    parser = Lark(decision_rule_grammar)

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

    decision_rule = SimpleRuleEngineLarkTreeAdapter(tree).get_rule()

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
        big_shot=True,
        pet="dog"
    )
    assert decision_rule.execute(token_dict=facts) is True

    facts = dict(
        cibil_score=600,
        age=40,
        house_ownership="owned",
        total_overdue_amount=100,
        number_of_overdue_loans=2,
        big_shot=False,
        pet="dog"
    )
    assert decision_rule.execute(token_dict=facts) is False
