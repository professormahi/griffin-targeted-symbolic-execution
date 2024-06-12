def escape_expression(expr: str) -> str:
    return str(expr) \
        .replace(">=", "&ge;") \
        .replace("<=", "&le;") \
        .replace(">", "&gt;") \
        .replace("<", "&lt;") \
        .replace("{", "\{") \
        .replace("}", "\}")
