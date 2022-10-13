from typing import Union

from simpleruleengine.conditional.conditional import Conditional
from simpleruleengine.conditional.when_all import WhenAll
from simpleruleengine.conditional.when_any import WhenAny
from simpleruleengine.expression.expression import Expression
from simpleruleengine.operator.between import Between
from simpleruleengine.operator.equal import Eq
from simpleruleengine.operator.greater_than import Gt
from simpleruleengine.operator.greater_than_equal import Gte
from simpleruleengine.operator.less_than import Lt
from simpleruleengine.operator.less_than_equal import Lte
from simpleruleengine.operator.operator import Operator
from simpleruleengine.operator.string_in import In
from simpleruleengine.operator.string_not_in import NotIn
from simpleruleengine.rule.rule import Rule
from simpleruleengine.rule.rule_decision import RuleDecision
from simpleruleengine.rule.rule_score import RuleScore
from simpleruleengine.rulerow.rule_row_decision import RuleRowDecision
from simpleruleengine.rulerow.rule_row_score import RuleRowScore
from simpleruleengine.ruleset.rule_set_decision import RuleSetDecision
from simpleruleengine.ruleset.rule_set_score import RuleSetScore
from simpleruleengine.token.numeric_token import NumericToken
from simpleruleengine.token.string_token import StringToken
from simpleruleengine.token.token import Token

from services.adapter.simple_rule_engine_adapter import SimpleRuleEngineAdapter


class SimpleRuleEngineDictAdapter(SimpleRuleEngineAdapter):
    def __init__(self, rule_dict: dict):
        super().__init__()
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

        # Parse as Score
        if "RuleScore" in self.rule_dict:
            rule_sets = self.rule_dict.get("RuleScore").get("RuleSets")
            rule_set_objects = []
            for rule_set in rule_sets:
                rule_row_objects = []
                rule_rows = rule_set.get("RuleRows")
                for rule_row in rule_rows:
                    rule_row_objects.append(
                        _get_rule_row_score(rule_row)
                    )

                rule_set_objects.append(
                    RuleSetScore(
                        *tuple(rule_row_objects),
                        weight=rule_set.get("Weight")
                    )
                )

            return RuleScore(
                *tuple(rule_set_objects)
            )


def _get_rule_row_score(rule_row: dict) -> RuleRowScore:
    return RuleRowScore(
        antecedent=_get_conditional(rule_row),
        consequent=rule_row.get("Consequent")
    )


def _get_rule_row_decision(rule_row: dict) -> RuleRowDecision:
    return RuleRowDecision(
        antecedent=_get_conditional(rule_row),
        consequent=rule_row.get("Consequent")
    )


def _get_conditional(rule_row: dict) -> Union[Conditional, Expression]:
    if "WhenAll" in rule_row:
        expressions = []
        for token in rule_row.get("WhenAll"):
            expressions.append(
                _get_conditional(token)
            )

        return WhenAll(*tuple(expressions))

    if "WhenAny" in rule_row:
        expressions = []
        for token in rule_row.get("WhenAny"):
            expressions.append(
                _get_conditional(token)
            )

        return WhenAny(*tuple(expressions))

    return _get_expression(rule_row)


def _get_expression(expression_dict: dict) -> Expression:
    token = _get_token(expression_dict)
    operator = _get_operator(expression_dict)

    assert token is not None
    assert operator is not None

    return Expression(token=token, operator=operator)


def _get_token(expression_dict: dict) -> Token:
    if "StringToken" in expression_dict:
        return StringToken(name=expression_dict.get("StringToken"))

    if "NumericToken" in expression_dict:
        return NumericToken(name=expression_dict.get("NumericToken"))


def _get_operator(expression_dict: dict) -> Operator:
    if "In" in expression_dict:
        return In(*tuple(expression_dict.get("In")))

    if "NotIn" in expression_dict:
        return NotIn(*tuple(expression_dict.get("NotIn")))

    if "Between" in expression_dict:
        return Between(
            floor=expression_dict.get("Between").get("floor"),
            ceiling=expression_dict.get("Between").get("ceiling")
        )

    if "Eq" in expression_dict:
        return Eq(expression_dict.get("Eq"))

    if "Lt" in expression_dict:
        return Lt(expression_dict.get("Lt"))

    if "Lte" in expression_dict:
        return Lte(expression_dict.get("Lte"))

    if "Gt" in expression_dict:
        return Gt(expression_dict.get("Gt"))

    if "Gte" in expression_dict:
        return Gte(expression_dict.get("Gte"))
