from slither.core.expressions.expression import Expression as SlitherExpression


def escape_expression(expr: SlitherExpression) -> str:
    return str(expr) \
        .replace(">=", "&ge;") \
        .replace("<=", "&le;") \
        .replace(">", "&gt;") \
        .replace("<", "&lt;")
