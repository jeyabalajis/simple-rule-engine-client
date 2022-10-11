from simpleruleengine.expression.expression import Expression


def expression_str(expression):
    expression_str = ""
    expression_str += expression.token.name + " "
    expression_str += type(expression.operator).__name__ + " "
    if type(expression.operator).__name__ == "Between":
        expression_str += str(expression.operator.floor) + ", " + str(expression.operator.ceiling)
    else:
        expression_str += str(expression.operator.base_value)

    return expression_str