import json

class GPTLibError(Exception):
    """Base exception class for the GPT Library."""
    pass

class FunctionNotFound(GPTLibError):
    """Exception raised when a function with a certain name is not found."""

    def __init__(self, function_name, arguments):
        self.function_name = function_name
        self.arguments = arguments
        message = f"Function '{function_name}' not found.\nargs: {arguments}"
        super().__init__(message)

class InvalidArgType(GPTLibError):
    """Exception raised when there's an error decoding JSON arguments."""

    def __init__(self, function_name, argument,**kwargs):
        self.function_name = function_name
        self.arguments = argument
        message = f"args: {argument} is {type(argument)} not a string!"
        super().__init__(message)
class ArgDecodeError(GPTLibError):
    """Exception raised when there's an error decoding JSON arguments."""

    def __init__(self, function_name, arguments,er,**kwargs):
        self.function_name = function_name
        self.arguments = arguments
        output=f" {er.msg} at line {er.lineno} column {er.colno}: `{arguments[er.pos]}`"
        message = f"ArgDecodeError for '{function_name}': {output} \n {arguments}"
        super().__init__(message,**kwargs)

class InvalidFuncArg(GPTLibError):
    """Exception raised when there's a mismatch in function arguments."""

    def __init__(self, message):
        super().__init__(message)
