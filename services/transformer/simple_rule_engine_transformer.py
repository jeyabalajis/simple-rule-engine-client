from lark import Transformer
from simpleruleengine.rule.rule_decision import RuleDecision

class SimpleRuleEngineTransformer(Transformer):
    def DecisionRule(self, args):
        print(args.data)
        return RuleDecision(*tuple(args))
