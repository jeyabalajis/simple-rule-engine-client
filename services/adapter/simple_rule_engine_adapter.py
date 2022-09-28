from simpleruleengine.expression.expression import Expression
from simpleruleengine.operator.between import Between
from simpleruleengine.rule.rule import Rule
from simpleruleengine.rule.rule_decision import RuleDecision
from simpleruleengine.rulerow.rule_row_decision import RuleRowDecision
from simpleruleengine.conditional.conditional import Conditional
from simpleruleengine.conditional.when_all import WhenAll
from simpleruleengine.conditional.when_any import WhenAny
from simpleruleengine.ruleset.rule_set_decision import RuleSetDecision
from simpleruleengine.token.token import Token
from simpleruleengine.token.string_token import StringToken
from simpleruleengine.token.numeric_token import NumericToken
from simpleruleengine.operator.string_in import In


class SimpleRuleEngineAdapter:
    def __init__(self, rule_dict: dict):
        self.rule_dict = rule_dict

    def get_rule(self) -> Rule:
        assert (
                "RuleDecision" in self.rule_dict or
                "RuleScore" in self.rule_dict
        )

        # Parse as Decision
        if "RuleDecision" in self.rule_dict:
            rule_row_objects = []
            rule_rows = self.rule_dict.get("RuleDecision").get("RuleRows")
            for rule_row in rule_rows:
                rule_row_objects.append(
                    _get_rule_row_decision(rule_row)
                )

            rule_set_objects = [RuleSetDecision(
                *tuple(rule_row_objects)
            )]

            return RuleDecision(
                *tuple(rule_set_objects)
            )


def _get_rule_row_decision(rule_row: dict) -> RuleRowDecision:
    return RuleRowDecision(
        antecedent=_get_conditional(rule_row),
        consequent=rule_row.get("Consequent")
    )


def _get_conditional(rule_row: dict):
    if "WhenAll" in rule_row:
        expressions = []
        for token in rule_row.get("WhenAll"):
            expressions.append(
                _get_conditional(token)
            )

        return WhenAll(*tuple(expressions))

    token = None
    operator = None
    if "StringToken" in rule_row:
        token = StringToken(name=rule_row.get("StringToken"))

        if "In" in rule_row:
            operator = In(*tuple(rule_row.get("In")))

    if "NumericToken" in rule_row:
        token = NumericToken(name=rule_row.get("NumericToken"))

        if "Between" in rule_row:
            operator = Between(
                floor=rule_row.get("Between").get("floor"),
                ceiling=rule_row.get("Between").get("ceiling")
            )

    assert token is not None
    assert operator is not None

    return Expression(token=token, operator=operator)
