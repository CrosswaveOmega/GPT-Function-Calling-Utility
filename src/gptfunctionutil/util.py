from typing import Dict, Any, Union
import sympy as sp
import openai
from .types import Ollama_ToolCall, OpenAI_ChatCompletionMessageToolCall


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


def append_id_if_present(
    out: Dict[str, Any],
    tool_call_object: Union[Ollama_ToolCall, OpenAI_ChatCompletionMessageToolCall],
) -> Dict[str, Any]:
    """Appends tool call id to output dictionary if tool_call_object is an openai tool call obj

    Args:
        out (Dict[str, Any]): output dictionary
        tool_call_object (Any): tool call object

    Returns:
        Dict[str, Any]: output dictionary
    """
    if hasattr(tool_call_object, "id"):
        out["tool_call_id"] = tool_call_object.id  # type: ignore
    return out
