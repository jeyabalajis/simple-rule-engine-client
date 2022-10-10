from lark import Transformer
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


class SimpleRuleEngineTransformer(Transformer):
    def expression(self, items):
        token = None
        if items[2].data == "number":
            token = NumericToken(items[0])

        if items[2].data in ("word_list", "string"):
            token = StringToken(items[0])
        
        operator = None
        if items[1].data == "between":
            operator = Between(floor=float(items[2].children[0].value), ceiling=float(items[3].children[0].value))
        
        print("Token: {} Operator: {}".format(token, operator))
        return Expression(token, operator)
            
