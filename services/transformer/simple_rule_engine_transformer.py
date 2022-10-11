from typing import List, Union

from lark import Tree, Token
from simpleruleengine.conditional.conditional import Conditional
from simpleruleengine.expression.expression import Expression
from simpleruleengine.operator.between import Between
from simpleruleengine.operator.string_in import In
from simpleruleengine.operator.equal import Eq
from simpleruleengine.operator.greater_than import Gt
from simpleruleengine.operator.greater_than_equal import Gte
from simpleruleengine.operator.less_than import Lt
from simpleruleengine.operator.less_than_equal import Lte
from simpleruleengine.rule.rule_decision import RuleDecision
from simpleruleengine.rulerow.rule_row_decision import RuleRowDecision
from simpleruleengine.ruleset.rule_set_decision import RuleSetDecision
from simpleruleengine.token.numeric_token import NumericToken
from simpleruleengine.token.string_token import StringToken
from simpleruleengine.rule.rule import Rule
from simpleruleengine.operator.operator import Operator
from services.util import simple_rule_engine_util


class SimpleRuleEngineTransformer:
    TREE = "Tree"
    TOKEN = "Token"
    DECISION_RULE = "decisionrule"
    EXPRESSION = "expression"
    NUMBER = "number"
    SIGNED_NUMBER = "SIGNED_NUMBER"
    STRING = "string"
    WORD = "WORD"
    BETWEEN  = "between"
    EQ = "eq"
    LTE = "lte"
    LT = "lt"
    GTE = "gte"
    GT = "gt"
    INLIST = "INLIST"

    def __init__(self, tree: Tree):
        self.tree = tree
        self._visited = {}

    def get_rule(self):
        """get_rule gets the root node of parse tree and processed it's children.
        Each child of the root node can be a decision rule or a score rule."""
        for rule in self.tree.children:
            if rule.data == self.DECISION_RULE:
                rule_decision = self._get_decision_rule(rule)

    def _get_decision_rule(self, rule: Tree) -> RuleDecision:
        """_get_decision_rule get a tree composed of a decision rule.
        It is composed [0] Rule Name and [1] 1 or more rule rows.
        """
        # Decision rule contains multiple children.
        # The first one is the rule name, followed by one or more rulerow.
        rule_name = rule.children[0]
        print("rule name: {}".format(rule_name))
        if (
                rule_name in self._visited and
                self._visited[rule_name] is True
        ):
            return

        rule_row_objects: List[RuleRowDecision] = []

        # Visit each rule row and get RuleRowDecision objects
        for rule_row in rule.children[1:]:
            rule_row_objects.append(self._get_rule_row_decision(rule_row))

        rule_set_objects = [RuleRowDecision(
            *tuple(rule_row_objects)
        )]

        return RuleDecision(
            *tuple(rule_set_objects)
        )

    def _get_rule_row_decision(self, rule_row: Tree) -> RuleRowDecision:
        """
        _get_rule_row_decision gets a rulerow node and returns RuleRowDecision post processing.
        """

        """
        rulerow contains 4 children namely 
        [0] "when"
        [1] condition
        [2] "then" 
        [3] decision.
        out of this, decision is processed for consequent and condition is processed for antecedent
        """
        antecedent = self._get_conditional(rule_row.children[1])
        consequent = self._get_consequent(rule_row.children[3])

    def _get_conditional(self, conditional: Tree) -> Conditional:
        """
        _get_conditional gets a condition node and returns a Conditional.
        Based on how expressions are strung togther, a complex Conditional must be formed.
        Examples: 
        1. a and b and c => WhenAll(a, b, c)
        2. a and b or c => WhenAny(WhenAll(a, b), c)
        3. a and b or (c and d) => WhenAny(WhenAll(a, b), WhenAll(c, d))
        """
        for child in conditional.children:
            if child.data == self.EXPRESSION:
                expression = self._get_expression(child)
            

    def _get_expression(self, expression: Tree) -> Expression:
        """
        _get_expression returns either an Expression or a Conditional (if the expression composes an expression)
        """
        # expression contains 3 or 4 children
        # [0] Token name 
        # [1] operator 
        # [2] base value
        # if operator is between, [2] is treated as floor and [3] is treated as ceiling
        # An expression can compose an expression, so this needs to be handled.

        if (
            type(expression.children[0]).__name__ == "Tree" and
            expression.children[0].data == self.EXPRESSION
        ):
            return self._get_conditional(expression)

        token = self._get_token(expression.children[0], expression.children[2])
        operator = self._get_operator(expression.children[1], type(token).__name__, *tuple(expression.children[2:]))
        expression = Expression(token=token, operator=operator)
        print("Expression: {}".format(simple_rule_engine_util.expression_str(expression)))
        return expression 


    def _get_token(self, token: Token, token_type: Token):
        token_type_str = token_type.children[0].type
        if token_type_str in (self.NUMBER, self.SIGNED_NUMBER):
            return NumericToken(token.value)

        if token_type_str in (self.STRING, self.WORD, "CNAME", "TRUE", "FALSE"):
            return StringToken(token.value)
        

    def _get_operator(self, operator: Union[Tree, Token], rule_engine_token_type: str, *base_value: Tree) -> Operator:
        """
        _get_operator returns an Operator.
        """
        if type(operator).__name__ == self.TREE:
            operator_type = operator.data
        else:
            operator_type = operator.type
        
        if operator_type == self.BETWEEN:
            return Between(
                floor=float(base_value[0].children[0].value), 
                ceiling=float(base_value[1].children[0].value)
            )
        
        if operator_type == self.INLIST:
            str_in_list:str = []
            for item in base_value:
                for child in item.children:
                    str_in_list.append(child.value)

            return In(*tuple(str_in_list))
        
        if operator_type == self.GT:
            operator_value = None
            for item in base_value:
                for child in item.children:
                    operator_value = float(child.value)
            
            assert operator_value is not None
            return Gt(operator_value)

        if operator_type == self.GTE:
            operator_value = None
            for item in base_value:
                for child in item.children:
                    operator_value = float(child.value)
            
            assert operator_value is not None
            return Gte(operator_value)

        if operator_type == self.EQ:
            operator_value = None
            for item in base_value:
                for child in item.children:
                    if rule_engine_token_type == "NumericToken":
                        operator_value = float(child.value)
                        assert operator_value is not None
                        return Eq(operator_value)

                    if rule_engine_token_type == "StringToken":
                        operator_value = str(child.value)
                        assert operator_value is not None
                        return In(*tuple([operator_value]))

        if operator_type == self.LT:
            operator_value = None
            for item in base_value:
                for child in item.children:
                    operator_value = float(child.value)
            assert operator_value is not None
            return Lt(operator_value)


    def _get_consequent(self, consequent: Tree):
        return self._get_token_value(consequent.children[0])

    def _get_token_value(self, token: Tree):
        if token.data == "boolean":
            return self._get_boolean(token.children[0])

        if token.data == "number":
            return self._get_number(token.children[0])

    def _get_boolean(self, boolean_token: Token):
        if boolean_token.value == "true":
            return True
        else:
            return False

    def _get_number(self, numeric_token: Token):
        return float(numeric_token.value)
