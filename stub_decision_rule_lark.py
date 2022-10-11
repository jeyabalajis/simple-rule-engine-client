from lark import Lark, Tree
from services.transformer.simple_rule_engine_transformer import SimpleRuleEngineTransformer

f = open("./decision_rule.lark").read()

parser = Lark(f)

text = """
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
            cibil_score < 650 or
            $RULE_overdue_rule < 0
        }
        then false
    }
    overdue_rule {
        when {
            overdue_in_months > 3
        }
        then -10
    }"""

tree = parser.parse(text)
print(tree.pretty())

# To do: Create an array of DecisionRule with name and Rule Rows condition
# The conditions must be evaluated to create a strategy of how WhenAll or WhenAny will be composed.
# Once this is done, everything can be collapsed into a single DecisionRule.


def walk_tree(tree, level=0):
    children = None
    try:
        children = tree.children
    except:
        pass

    data = None
    try:
        data = "{} {} with {} children {}".format(type(tree).__name__, tree.data, len(children))   
    except:
        data = "{} {}".format(type(tree).__name__, tree)

    print("Data: {}, Level: {}".format(data, level))

    if children is None:
        return

    _level = level + 1
    tokens = []
    tree_children = []
    for child in children:
        if type(child).__name__ == "Token":
            tokens.append(child)
        
        if type(child).__name__ == "Tree":
            tree_children.append(child)
    print("tokens: {}".format(tokens))
    for child in tree_children:
        walk_tree(child, _level)
    

# walk_tree(rule)

SimpleRuleEngineTransformer(tree).get_rule()
