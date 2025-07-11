from __future__ import annotations


import inspect
import json
import re
from typing import Any, Callable, Coroutine, Dict, List, Union

from enum import Enum, EnumMeta

from datetime import datetime

from gptfunctionutil.types import AsyncFunction, DecoratedFunction, FunctionCall_Dict, NameArgsTuple, ToolCall_Union

from .errors import *
from .convertutil import ConvertStatic
from .logger import logs

from .util import parse_expression, append_id_if_present


class CommandSingleton:
    _instance = None
    _commands = {}

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance

    @staticmethod
    def add_command(name, command):
        CommandSingleton._commands[name] = command

    @staticmethod
    def load_command(name):
        return CommandSingleton._commands.get(name, None)


def sync_not_implemented(*args, **kwargs):
    raise NotImplementedError("Sync method not added.")


async def async_not_implemented(*args, **kwargs):
    """
    An asynchronous placeholder function that raises a NotImplementedError.

    This function is intended to be used as a stub for asynchronous methods
    that have not yet been implemented. It accepts any arguments and keyword
    arguments but does not perform any operations.

    Args:
        *args: Variable-length positional arguments.
        **kwargs: Arbitrary keyword arguments.

    Raises:
        NotImplementedError: Always raised to indicate the method is not implemented.
    """
    raise NotImplementedError("Async method not added.")


class LibCommand:
    """This class is a container for functions that have been annotated with the
     LibParam and the AILibFunction decorators,
    wrapping them up with attributes that help the GPTFunctionLibary invoke them."""

    def __init__(
        self,
        func: Union[Callable, AsyncFunction],
        name: str,
        description: str,
        required: List[str] = [],
        force_words: List[str] = [],
        enabled=True,
        strict=False,
    ):
        """
        This class represents a library command. It encapsulates a callable method/coroutine,
        along with its associated metadata and functionality.

        Args:
            func (Union[callable,Coroutine]): The callable method or coroutine to be wrapped.
            name (str): The name of the command.
            description (str): The description of the command.
            required (List[str], optional): A list of required parameter names. Defaults to an empty list.
            force_words (List[str], optional): A list of force words. Defaults to an empty list.
            enabled (bool, optional): Indicates whether the command is enabled. Defaults to True.
        """
        self.command = func
        self.syncr: Callable = sync_not_implemented
        self.asyncr: AsyncFunction = async_not_implemented
        self.internal_name = self.function_name = name
        self.comm_type = "callable"

        if inspect.iscoroutinefunction(func):
            self.comm_type = "coroutine"
            self.asyncr = func
        else:
            self.syncr = func  # type: ignore
        logs.info("initalizing %s, comm type is %s", self.function_name, self.comm_type)
        my_schema = {
            "name": self.function_name,
            "description": description,
            "parameters": {"type": "object", "properties": {}, "required": []},
            "strict": strict,
        }

        self.function_schema = my_schema
        self.required = required

        self.param_converters = {}
        self.param_iterate()

        self.enabled = enabled
        self.force_words = force_words
        self.strict = strict

    def param_iterate(self):
        """
        Iterates over the command's arguments and update the function_schema
        dictionary with parameter information.
        Every parameter that is not decorated with a valid type will not be added!
        """
        func: DecoratedFunction = self.command  # type: ignore
        paramdict = {}
        param_decorators = {}

        sig = inspect.signature(func)
        if hasattr(func, "parameter_decorators"):
            paramdict = sig.parameters
            param_decorators = func.parameter_decorators

        self.function_schema.update({"parameters": {"type": "object", "properties": {}, "required": []}})
        for param_name, param in paramdict.items():
            decs = param_decorators.get(param_name, "")

            param_info, converter = ConvertStatic.parameter_into_schema(param_name, param, dec=decs)

            if param_info is not None:
                self.param_converters[param_name] = converter
                self.function_schema["parameters"]["properties"][param_name] = param_info
                if param.default == inspect.Parameter.empty or param_name in self.required:
                    self.function_schema["parameters"]["required"].append(param_name)

            # if isinstance(param.annotation, str):
            #     typename = param.annotation  # Treat the string annotation as a regular string
            # else:
            #     typename = param.annotation.__name__  # Access the __name__ attribute of the type object

            # oldtypename=typename
            # if typename in substitutions:
            #     typename=substitutions[typename]
            # else:
            #     continue
            # param_info = {
            #     'type': typename,
            #     'description': param_decorators.get(param_name, '')
            # }
            # if typename in to_ignore:
            #     continue
            # if oldtypename== 'datetime':
            #     param_info['format']='date-time'
            # if oldtypename == 'Literal':
            #     literal_values = param.annotation.__args__
            #     param_info['enum'] = literal_values
            # self.function_schema['parameters']['properties'][param_name] = param_info
            # if param.default == inspect.Parameter.empty or param_name in self.required:
            #     self.function_schema['parameters']['required'].append(param_name)

    def convert_args(self, function_args: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and convert all arguments within function_args
        with the Converters.

        Args:
            function_args (Dict[str, Any]): A dictionary containing the function arguments,
            returned by the LLM of your choice.

        Returns:
            Dict[str, Any]: The converted function argument dictionary.
        """
        schema = self.function_schema
        parameters = schema["parameters"]
        logs.info(
            "converting args for function %s, args:%s",
            self.function_name,
            function_args,
        )

        for i, v in parameters["properties"].items():
            if i in function_args:
                converter = self.param_converters[i]

                result = ConvertStatic.schema_validate(i, function_args[i], v, converter)

                logs.info("arg %s converted into %s", i, result)
                function_args[i] = result
        return function_args

    def check_force(self, query: str) -> bool:
        """
        Checks if the given query contains any of the command's force words.

        Args:
           query (str): The query to be checked.

        Returns:

            bool: True if the query contains force words, False otherwise.
        """
        if self.force_words:
            pattern = r"\b(?:{})\b".format("|".join(map(re.escape, self.force_words)))
            regex = re.compile(pattern, re.IGNORECASE)
            match = regex.search(query)
            if match:
                return True
        return False


class GPTFunctionLibrary:
    """
    A collection of methods to be used with OpenAI's chat completion endpoint.
    When subclassed, decorated methods, called LibCommands, will be added to an internal FunctionDict along with
    a special LibCommand object
    All methods will be converted to a function schema dictionary, which will be sent to OpenAI along with any user text.
    OpenAI will then format paramaters and return them within a JSON object, which will be used to trigger the method
    with call_by_dict or call_by_dict_ctx for discord.py Bot Commands.

    It's possible to use both subclassed methods and discord.py Bot Commands
    so long as either are decorated with the AILibFunction and LibParam decorators.
    Bot Commands can be defined in any Cog, so long as add_in_commands is called at least once before
    the GPTFunctionLibrary is used with the API.

    Attributes:
        FunctionDict ( Dict[str, Union[Command,callable]]): A dictionary mapping command and method names to the corresponding Command or methods
    """

    def __init__(self):
        self.FunctionDict: Dict[str, LibCommand] = {}
        self.do_expression = False

        self._update_function_dict()

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        """
        Override the __new__ method to update the FunctionDict when instantiating or subclassing.

        Returns:
            The new instance of the class.
        """
        new_cls = super().__new__(cls, *args, **kwargs)
        # new_cls._update_function_dict()
        return new_cls

    def _update_function_dict(self) -> None:
        """
        Update the FunctionDict with decorated methods from a descended class.

        This method iterates over the class's methods and adds the ones with function schema to the FunctionDict.
        """
        for name, method in self.__class__.__dict__.items():
            if hasattr(method, "libcommand"):
                function_name = method.libcommand.function_name or method.__name__
                logs.info(
                    "adding %s: '%s' into %s function_dictionary",
                    method.libcommand.comm_type,
                    function_name,
                    self.__class__.__name__,
                )
                self.FunctionDict[function_name] = method.libcommand

    def force_word_check(self, query: str):
        """
        Check if the query contains the force words of any command.
        force words will force OpenAI to invoke THAT particular command, as opposed to
        invoking a command automatically.
        """
        functions_with_schema = []
        for name, method in self.FunctionDict.items():
            schema = None
            comm = method

            if comm:
                if comm.check_force(query):
                    schema = comm.function_schema
                    new = {"type": "function", "function": schema}
                    return [new]
        return None

    def get_schema(self) -> List[Dict[str, Any]]:
        """
        Get the list of function schema dictionaries representing callable methods, coroutines, or bot Commands available to the library.

        Returns:
            A list of function schema dictionaries from each decorated method or Command
        """
        functions_with_schema = []
        for name, libmethod in self.FunctionDict.items():
            schema = None
            if libmethod.enabled:
                schema = libmethod.function_schema
            if schema != None:
                if schema.get("parameters", None) != None:
                    functions_with_schema.append(schema)
        return functions_with_schema

    def get_tool_schema(self) -> List[Dict[str, Any]]:
        """
        Get the list of function schema dictionaries representing callable methods, coroutines, or bot Commands available to the library.

        Returns:
            A list of function schema dictionaries from each decorated method or Command
        """
        functions_with_schema = []
        for name, libmethod in self.FunctionDict.items():
            schema = None
            if libmethod.enabled:
                schema = libmethod.function_schema
            if schema != None:
                if schema.get("parameters", None) != None:
                    new = {"type": "function", "function": schema}
                    functions_with_schema.append(new)
        return functions_with_schema

    def expression_match(self, function_args: str):
        """because sometimes, the API returns an expression and not a single integer."""
        if self.do_expression:
            """In case I want to change how I want to parse expressions later."""
            expression_detect_pattern = r'(?<=:\s)([^"]*?[+\-*/][^"]*?)(?=(?:,|\s*\}))'
            return re.sub(
                expression_detect_pattern,
                lambda m: parse_expression(m.group()),
                function_args,
            )
        return function_args

    def parse_name_args(self, function_dict: FunctionCall_Dict) -> NameArgsTuple:
        """Parse the args within function_dict, and apply any needed corrections to the JSON."""
        function_name: str = function_dict.get("name", "")
        function_args: Union[str, Dict[str, Any], None] = function_dict.get("arguments", None)

        if function_name in self.FunctionDict:
            if isinstance(function_args, str):
                # Making it so it won't break on poorly formatted function arguments.
                function_args = function_args.replace("\\n", "\n")
                quoteescapefixpattern: str = r"(?<=:\s\")(.*?)(?=\"(?:,|\s*\}))"
                # In testing, I once had the API return a poorly escaped function_args attribute
                # That could not be parsed by json.loads, so hence this regex.
                function_args_str: str = re.sub(
                    quoteescapefixpattern,
                    lambda m: m.group().replace('"', r"\""),
                    function_args,
                )

                # This regex is for detecting if there's an expression as a value and not a single integer.
                # Which has happened before during testing.
                function_args_str = self.expression_match(function_args_str)
                logs.info(
                    "transformed json args for func %s.  result:\n%s",
                    function_name,
                    function_args_str,
                )
                try:
                    function_args = json.loads(function_args_str, strict=False)
                except json.JSONDecodeError as e:
                    # Something went wrong while parsing, return where.
                    output: str = (
                        f"JSONDecodeError: {e.msg} at line {e.lineno} column {e.colno}: `{function_args_str[e.pos]}`"
                    )
                    raise ArgDecodeError(
                        function_name=function_name,
                        arguments=function_args_str,
                        msg=f"{output}",
                        er=e,
                    ) from e
            return function_name, function_args

        raise FunctionNotFound(function_name=function_name, arguments=function_args)

    def convert_args(self, function_name: str, function_args: Dict[str, Any]) -> Dict[str, Any]:
        """Preform any needed conversion of the function arguments."""
        libmethod = self.FunctionDict[function_name]

        return libmethod.convert_args(function_args)

    def default_callback(self, function_name: str, function_args: str = "NONE") -> str:
        """This is called whenever an invalid function is called."""
        output = f"{function_name} is not a valid function."
        function_args = function_args.replace("\\n", "\n")
        output += "\n```{function_args}```"
        return output

    def call_by_dict(self, function_dict: FunctionCall_Dict) -> Any:
        """
        Call a function based on the provided dictionary.

        Args:
            function_dict (Dict[str, Any]): The dictionary containing the function name and arguments.

        Returns:
            The result of the function call.

        Raises:
            AttributeError: If the function name is not found or not callable.
        """
        try:
            function_name, function_args = self.parse_name_args(function_dict)
        except GPTLibError as e:
            if isinstance(e, FunctionNotFound):
                """Invoke a default function so something is returned..."""
                return self.default_callback(e.function_name, e.arguments)

            result = str(e)
            return result

        libmethod = self.FunctionDict.get(function_name)
        if not libmethod:
            raise AttributeError(f"Method '{function_name}' not found or not callable.")

        if libmethod.comm_type == "callable":
            function_args = libmethod.convert_args(function_args)
            if len(function_args) > 0:
                # for i, v in function_args.items():
                #    print("st",i,v)
                return libmethod.command(self, **function_args)
            return libmethod.command(self)
        else:
            raise AttributeError(f"Method '{function_name}' not found or not callable.")

    async def call_by_dict_async(self, function_dict: FunctionCall_Dict):
        """
        Call an function based on the provided dictionary.
        This function works with coroutines.

        Args:
            function_dict (Dict[str, Any]): The dictionary containing the function name and arguments.

        Returns:
            The result of the function call.

        Raises:
            AttributeError: If the function name is not found or not callable.
        """
        try:
            function_name, function_args = self.parse_name_args(function_dict)
        except GPTLibError as e:
            if isinstance(e, FunctionNotFound):
                """Invoke a default function so something is returned..."""
                return self.default_callback(e.function_name, e.arguments)

            result = str(e)
            return result
        libmethod = self.FunctionDict.get(function_name)
        if not libmethod:
            raise AttributeError(f"Method '{function_name}' not found or not callable.")

        if libmethod.comm_type == "coroutine":
            if len(function_args) > 0:
                return await libmethod.asyncr(self, **function_args)
            return await libmethod.asyncr(self)

        elif libmethod.comm_type == "callable":
            function_args = libmethod.convert_args(function_args)
            if len(function_args) > 0:
                return libmethod.syncr(self, **function_args)
            return libmethod.syncr(self)
        else:
            raise AttributeError(f"Method '{function_name}' not found or not callable.")

    def call_by_tool(self, tool_call: ToolCall_Union):
        """
        Call a function based on the syntax from the tool object.

        Args:
            tool_call (ChatCompletionMessageToolCall): Tool parameters returned by openai

        Returns:
            The result of the function call.

        Raises:
            AttributeError: If the function name is not found or not callable.
        """
        function_name = tool_call.function.name

        function_args = tool_call.function.arguments
        dictv = {"name": function_name, "arguments": function_args}
        function_response = self.call_by_dict(dictv)
        out = {
            "role": "tool",
            "name": function_name,
            "content": function_response,
        }
        return append_id_if_present(out, tool_call)

    async def call_by_tool_async(self, tool_call: ToolCall_Union):
        """
        Asyncio version of call by tool.
        Call a function based on the syntax from the tool object.
        works with coroutines.

        Args:
            tool_call (ChatCompletionMessageToolCall): Tool parameters returned by openai

        Returns:
            The result of the function call.

        Raises:
            AttributeError: If the function name is not found or not callable.
        """
        function_name = tool_call.function.name

        function_args = tool_call.function.arguments
        dictv = {"name": function_name, "arguments": function_args}
        function_response = await self.call_by_dict_async(dictv)
        out = {
            "role": "tool",
            "name": function_name,
            "content": function_response,
        }
        return append_id_if_present(out, tool_call)


def genspec(name: str, description: str, **kwargs):
    spec = {}
    spec[name] = {}
    spec[name]["description"] = description
    spec[name].update(kwargs)
    return spec


def LibParamSpec(name: str, description: str, **kwargs):
    """
    A much more advanced variant of LibParam.  Set a function's description as well as
    additional arguments depending on the schema's type.
    For instance, you can restrict a string's length with "minLength" and  "maxLength",
    set the minimum and maximum of a number with 'minimum' and 'maximum', and more.

    AILibFunctions without this decorator will not be sent to the AI.
    Args:
        name: name of the parameter to apply description to.
        description: description to be applied to the parameter.
        **kwargs: a function's parameters, and the description to be applied to each.
    Returns:
        The decorated function.
    """

    def decorator(func: DecoratedFunction) -> DecoratedFunction:
        if not hasattr(func, "parameter_decorators"):
            func.parameter_decorators = {}
        gen = genspec(name, description, **kwargs)
        func.parameter_decorators.update(gen)
        return func

    return decorator


def LibParam(**kwargs: Any) -> Any:
    """
    Decorator to add descriptions to any valid parameter inside a GPTFunctionLibary method.
    AILibFunctions without this decorator will not be sent to the AI.
    Args:
        **kwargs: a function's parameters, and the description to be applied to each.
    Returns:
        The decorated function.
    """

    def decorator(func: DecoratedFunction) -> DecoratedFunction:
        if not hasattr(func, "parameter_decorators"):
            func.parameter_decorators = {}
        func.parameter_decorators.update(kwargs)
        return func

    return decorator


def AILibFunction(
    name: str,
    description: str,
    required: List[str] = [],
    force_words: List[str] = [],
    enabled=True,
    strict=False,
) -> Any:
    """
    Flags a callable method, Coroutine, or discord.py Command, creating a LibCommand object.
    In the case of a bot Command, the schema is added into the Command.extras attribute.
    Only Commands decorated with this can be called by the AI.

    This should always be above the command decorator:
    @AILibFunction(...)
    @LibParam(...)
    @commands.command(...,extras={})
    Args:
        name (str): The name of the function.
        description (str): The description of the function.
        required:List[str]: list of parameters you want the AI to always use reguardless of if they have defaults.
        force_words:List[str]: list of words that will be used to force this command to be triggered.
        enabled (bool): Whether or not this function is enabled by default.
        strict (bool): Whether to enable strict schema adherence when generating the function call.
            If set to true, the model will follow the exact schema defined in the parameters field.
            Only a subset of JSON Schema is supported when strict is true
    Returns:
        callable, Coroutine, or Command.
    """

    def decorator(func: DecoratedFunction):
        mycommand = LibCommand(func, name, description, required, force_words, enabled, strict)
        func.libcommand = mycommand

        return func

    return decorator
