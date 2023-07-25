import json
from .logger import logs
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

class ConversionError(GPTLibError):
    """Exception raised when Something went wrong when converting/validating a responce."""

    def __init__(self, message):
        super().__init__(message)

class ConversionToError(ConversionError):

    def __init__(self, param_name='', param='', schema={}, msg=''):
        self.param_name=param_name
        self.param=''
        self.dec=schema
        message=f"{msg} Param:{param_name} of type {param}.\n could not be converted into a schema!"
        super().__init__(message)


class ConversionAddError(ConversionError):

    def __init__(self, msg=''):
        super().__init__(msg)


class ConversionFromError(ConversionError):

    def __init__(self, param_name='', value='', schema={}, msg=''):
        self.param_name=param_name
        self.value=value
        self.schema=schema
        message=f"{msg} Param:{param_name}. Value{value}.\n Schema:{str(schema)}"
        super().__init__(message)

