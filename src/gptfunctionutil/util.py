import sympy as sp


def parse_expression(expression_str: str) -> sp.Expr:
    """
    Evaluates a mathematical expression given as a string and returns the numerical result.
    This is just in case the AI returns a math expression.

    Parameters:
    - expression_str: A string representation of the mathematical expression to evaluate.

    Returns:
    The numerical result of the expression.
    """

    expr = sp.sympify(expression_str)
    numerical_result = expr.evalf()
    return numerical_result
