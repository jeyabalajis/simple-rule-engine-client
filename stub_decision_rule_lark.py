from lark import Lark, Tree

f = open("./decision_rule.lark").read()

parser = Lark(f)

text = """
    DecisionRule my_rule {
        when {
            cibil_score >= 650 and 
            age > 35 and 
            house_ownership in (owned, rented) and 
            pet == dog
        }
        then true
        when {
            cibil_score < 650 or
            $RULE_overdue_rule < 0
        }
        then false
    }
    DecisionRule overdue_rule {
        when {
            overdue_in_months > 3
        }
        then -10
    }"""

tree = parser.parse(text)
print(tree.pretty())

