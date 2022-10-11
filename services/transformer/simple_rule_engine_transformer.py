from typing import List

from lark import Tree, Token
from simpleruleengine.conditional.conditional import Conditional
from simpleruleengine.expression.expression import Expression
from simpleruleengine.operator.between import Between
from simpleruleengine.rule.rule_decision import RuleDecision
from simpleruleengine.rulerow.rule_row_decision import RuleRowDecision
from simpleruleengine.ruleset.rule_set_decision import RuleSetDecision
from simpleruleengine.token.numeric_token import NumericToken
from simpleruleengine.token.string_token import StringToken
from simpleruleengine.rule.rule import Rule


class SimpleRuleEngineTransformer:
    DECISION_RULE = "decisionrule"

    def __init__(self, tree: Tree):
        self.tree = tree
        self._visited = {}

    def get_rule(self):
        print(self.tree.data)
        for rule in self.tree.children:
            if rule.data == self.DECISION_RULE:
                rule_decision = self._get_decision_rule(rule)

    def _get_decision_rule(self, rule: Tree) -> RuleDecision:
        rule_name = rule.children[0]
        print("rule name: {}".format(rule_name))
        if (
                rule_name in self._visited and
                self._visited[rule_name] is True
        ):
            return

        rule_row_objects: List[RuleRowDecision] = []
        for rule_row in rule.children[1:]:
            rule_row_objects.append(self._get_rule_row_decision(rule_row))

        rule_set_objects = [RuleSetDecision(
            *tuple(rule_row_objects)
        )]

        return RuleDecision(
            *tuple(rule_set_objects)
        )

    def _get_rule_row_decision(self, rule_row: Tree) -> RuleRowDecision:
        antecedent = self._get_conditional(rule_row.children[1])
        consequent = self._get_consequent(rule_row.children[3])

    def _get_conditional(self, conditional: Tree) -> Conditional:
        pass

    def _get_expression(self, expression: Tree) -> Expression:
        pass

    def _get_consequent(self, consequent: Tree):
        return self._get_token_value(consequent.children[0])

    def _get_token_value(self, token: Tree):
        print("Token {} {}".format(type(token).__name__, token.data))
        if token.data == "boolean":
            return self._get_boolean(token.children[0])

        if token.data == "number":
            return self._get_number(token.children[0])

    def _get_boolean(self, boolean_token: Token):
        print("Value: {}".format(boolean_token.value))
        if boolean_token.value == "true":
            return True
        else:
            return False

    def _get_number(self, numeric_token: Token):
        return float(numeric_token.value)
