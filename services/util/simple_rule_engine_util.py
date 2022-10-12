from simpleruleengine.conditional.conditional import Conditional
from simpleruleengine.expression.expression import Expression


def expression_pretty(expression: Expression):
    expression_string = ""
    expression_string += expression.token.name + " "
    expression_string += type(expression.operator).__name__ + " "
    if type(expression.operator).__name__ == "Between":
        expression_string += str(expression.operator.floor) + ", " + str(expression.operator.ceiling)
    else:
        expression_string += str(expression.operator.base_value)

    return expression_string


def conditional_pretty(conditional: Conditional, depth=0):
    conditional_string = type(conditional).__name__ + "("

    for child in conditional.expressions:
        if type(child).__name__ in ("WhenAll", "WhenAny"):
            conditional_string += "(" + conditional_pretty(child, depth + 1) + "), "

        if type(child).__name__ in "Expression":
            conditional_string += "{" + expression_pretty(child) + "}, "

    conditional_string += ")"

    return conditional_string
