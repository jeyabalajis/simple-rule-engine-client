from typing import List, Union

from lark import Tree, Token
from simpleruleengine.conditional.conditional import Conditional
from simpleruleengine.conditional.when_all import WhenAll
from simpleruleengine.conditional.when_any import WhenAny
from simpleruleengine.expression.expression import Expression
from simpleruleengine.rule.rule_decision import RuleDecision
from simpleruleengine.rulerow.rule_row_decision import RuleRowDecision
from simpleruleengine.ruleset.rule_set_decision import RuleSetDecision
from simpleruleengine.token.numeric_token import NumericToken
from simpleruleengine.token.string_token import StringToken
from simpleruleengine.token.boolean_token import BooleanToken
from simpleruleengine.rule.rule import Rule
from simpleruleengine.operator.operator import Operator

from services.adapter.simple_rule_engine_adapter import SimpleRuleEngineAdapter
from services.util import simple_rule_engine_util
from queue import Queue


class SimpleRuleEngineLarkTreeAdapter(SimpleRuleEngineAdapter):
    TREE = "Tree"
    TOKEN = "Token"
    DECISION_RULE = "decisionrule"
    EXPRESSION = "expression"
    CONDITIONAL = "conditional"
    NUMBER = "number"
    SIGNED_NUMBER = "SIGNED_NUMBER"
    STRING = "string"
    WORD = "WORD"
    BETWEEN = "between"
    EQ = "eq"
    LTE = "lte"
    LT = "lt"
    GTE = "gte"
    GT = "gt"
    IN_LIST = "INLIST"
    CONDITIONAL_AND = "and"
    CONDITIONAL_OR = "or"

    def __init__(self, tree: Tree):
        super().__init__()
        self.lark_tree = tree
        self._visited = {}

    def get_rule(self) -> Rule:
        """get_rule gets the root node of parse lark_tree and processes it's children.
        Each child of the root node can be a decision rule or a score rule."""
        for rule in self.lark_tree.children:
            if rule.data == self.DECISION_RULE:
                return self._get_decision_rule(rule)

    def _get_decision_rule(self, rule: Tree) -> RuleDecision:
        """_get_decision_rule gets a lark_tree composed of a decision rule.
        It is composed a Rule Name and 1 or more rule rows.
        Structure of a decision rule:
        decisionrule
            rule name
            rulerow
            rulerow
            rulerow...
        """
        # Decision rule contains multiple children.
        # The first one is the rule name, followed by one or more rule_row.
        rule_name = rule.children[0]
        if rule_name in self._visited:
            return self._visited[rule_name]["rule"]

        rule_row_objects: List[RuleRowDecision] = []

        # Visit each rule row and get RuleRowDecision objects
        for rule_row in rule.children[1:]:
            rule_row_objects.append(self._get_rule_row_decision(rule_row))

        rule_set_objects = [RuleSetDecision(
            *tuple(rule_row_objects)
        )]

        rule_decision: RuleDecision = RuleDecision(
            *tuple(rule_set_objects)
        )

        self._visited[rule_name] = dict(rule=rule_decision)
        return rule_decision

    def _get_rule_row_decision(self, rule_row: Tree) -> RuleRowDecision:
        """
        _get_rule_row_decision gets a rulerow node and returns RuleRowDecision post processing.
        Structure of rulerow
        rulerow
            when
            condition
            then
            decision
        """

        """
        rulerow contains 4 children namely 
        - "when"
        - condition: A condition that's composed of a series of expressions strung together by and / or.
        - "then" 
        - decision.
        out of this, decision is processed for consequent and condition is processed for antecedent
        """
        antecedent = self._get_conditional(rule_row.children[1])
        consequent = simple_rule_engine_util.get_consequent(rule_row.children[3])

        return RuleRowDecision(antecedent=antecedent, consequent=consequent)

    def _get_conditional(self, conditional: Tree) -> Conditional:
        """
        _get_conditional gets a condition node and returns a Conditional.
        Structure of condition
        condition
            expression
            conditional and/or (optional)
            expression and/or (optional)
            expression
        """
        conditional_queue = Queue()
        expression_queue = Queue()
        for child in conditional.children:
            if child.data == self.EXPRESSION:
                expression_queue.put(self._get_expression(child))

            if child.data == self.CONDITIONAL:
                conditional_queue.put(child.children[0].value)

        return self._get_composite_conditional(
            conditional_queue=conditional_queue,
            expression_queue=expression_queue
        )

    def _get_composite_conditional(self, *, conditional_queue: Queue, expression_queue: Queue) -> Conditional:
        """
        _get_composite_conditional forms a complex Conditional based on how expressions are strung together
        Examples:
        1. a and b and c => WhenAll(a, b, c)
        2. a and b or c => WhenAny(WhenAll(a, b), c)
        3. a and b or (c and d) => WhenAny(WhenAll(a, b), WhenAll(c, d))
        4. a and b and (c and d or (e and f)) => WhenAll(a, b, WhenAny(WhenAll(c, d), WhenAll(e, f)))
        :param conditional_queue:
        :param expression_queue:
        :return: Conditional
        """
        # Pop conditional queue and combine expressions into a single Conditional
        # Assumption: For one conditional, there would be two expressions.
        final_conditional = None

        # If this is a single expression, wrap this under WhenAll and return 
        if conditional_queue.empty():
            return WhenAll(expression_queue.get())

        while not conditional_queue.empty():
            current_conditional = conditional_queue.get()
            if current_conditional == self.CONDITIONAL_AND:
                if final_conditional is None:
                    final_conditional = WhenAll(expression_queue.get(), expression_queue.get())
                else:
                    final_conditional = WhenAll(final_conditional, expression_queue.get())

            if current_conditional == self.CONDITIONAL_OR:
                if final_conditional is None:
                    final_conditional = WhenAny(expression_queue.get(), expression_queue.get())
                else:
                    final_conditional = WhenAny(final_conditional, expression_queue.get())

        return final_conditional

    def _get_expression(self, expression: Tree) -> Union[Expression, Conditional]:
        """
        _get_expression returns either an Expression or a Conditional (if the expression contains an expression)
        Structure of expression
        expression
            token
            operator
            base value
        (or)
        expression
            expression
        """
        # expression contains either 3 children or 4 children (if operator is between)
        # - Token name 
        # - operator 
        # - base value
        # if the operator is between, [2] is treated as floor and [3] is treated as ceiling

        # If an expression composes another expression, get this as a Conditional.
        if (
                type(expression.children[0]).__name__ == self.TREE and
                expression.children[0].data == self.EXPRESSION
        ):
            return self._get_conditional(expression)

        token = self._get_token(expression.children[0], expression.children[2])
        operator = self._get_operator(
            *tuple(expression.children[2:]),
            operator=expression.children[1],
            rule_engine_token_type=type(token).__name__
        )
        expression = Expression(token=token, operator=operator)
        return expression

    def _get_token(self, token: Tree, token_type: Tree):
        """
        _get_token returns a Simple Rule Engine Token from a lark Tree. Return a specific token (StringToken or
        NumericToken or BooleanToken) based on the base value that's composed within the expression.
        """
        token_type_str = token_type.children[0].type
        if token_type_str in (self.NUMBER, self.SIGNED_NUMBER):
            return NumericToken(name=token.children[0].value)

        if token_type_str in (self.STRING, self.WORD, "CNAME"):
            return StringToken(name=token.children[0].value)

        if token_type_str in ("TRUE", "FALSE"):
            return BooleanToken(name=token.children[0].value)

    def _get_operator(self, *base_value: Tree, operator: Union[Tree, Token], rule_engine_token_type: str, ) -> Operator:
        """
        _get_operator returns an Operator based on operator type and token type
        (StringToken, NumericToken or BooleanToken).
        """

        operator_type = operator.data if type(operator).__name__ == self.TREE else operator.type

        if operator_type == self.BETWEEN:
            return simple_rule_engine_util.get_between(*base_value)

        if operator_type == self.IN_LIST:
            return simple_rule_engine_util.get_list_in(base_value)

        if operator_type == self.GT:
            return simple_rule_engine_util.get_greater_than(base_value)

        if operator_type == self.GTE:
            return simple_rule_engine_util.get_greater_than_equal(base_value)

        if operator_type == self.EQ:
            return simple_rule_engine_util.get_equal(base_value, rule_engine_token_type)

        if operator_type == self.LT:
            return simple_rule_engine_util.get_less_than(base_value)

        if operator_type == self.LTE:
            return simple_rule_engine_util.get_less_than_equal(base_value)
