import inspect
import json
import re
from typing import Any, Coroutine, Dict, List, Union

from enum import Enum, EnumMeta

from datetime import datetime
from discord.ext.commands import (
    Command,
    Context,
    Bot,
    CommandNotFound,
    CheckFailure
)
from .functionlib import GPTFunctionLibrary, LibCommand

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

substitutions={
    'str':'string',
    'int':'integer',
    'bool':'boolean',
    'float':'number',
    'datetime':'string',
    'Literal':'string'
}
class LibCommandDisc(LibCommand):
    '''This class is a container for functions, coroutines, and discord.py Commands
    that have been annotated with the LibParam and the AILibFunction decorators,
    wrapping them up with attributes that help the GPTFunctionLibary invoke them.'''
    def __init__(self, func: Union[Command,callable,Coroutine], name: str, description: str, required:List[str]=[],force_words:List[str]=[], enabled=True):
        '''
        Description: This class represents a library command. It encapsulates a Discord bot command, along with its associated metadata and functionality.

        Args:
            func (Command): The Discord.py bot command object. (commands.command())
            name (str): The name of the command.
            description (str): The description of the command.
            required (List[str], optional): A list of required parameter names. Defaults to an empty list.
            force_words (List[str], optional): A list of force words. Defaults to an empty list.
            enabled (bool, optional): Indicates whether the command is enabled. Defaults to True.
        '''
        self.command=func
        self.internal_name=self.function_name=name
        self.comm_type='callable'

        if isinstance(func, Command):
            self.function_name=func.qualified_name
            self.comm_type='command'

            print(self.function_name,self.comm_type)
            my_schema= {
                'name': self.function_name,
                'description': description,
                'parameters':{'type': 'object','properties': {},'required': []}
            }

            self.function_schema=my_schema
            self.required=required
            #if 'parameter_decorators' in func.extras:
            self.param_iterate()
            self.enabled=enabled
            self.force_words=force_words
        else:
            super().__init__(func, name, description, required,force_words,enabled)
    def param_iterate(self):
        '''
        Iterates over the command's arguments and update the function_schema dictionary with parameter information.
        Every parameter that isn't 'self' or ctx must be added!
        '''
        func=self.command
        paramdict={}
        param_decorators={}
        if self.comm_type=='command':
            if 'parameter_decorators' in func.extras:
                paramdict=func.clean_params
                param_decorators=func.extras['parameter_decorators']
        else:
            sig = inspect.signature(func)
            if hasattr(func,'parameter_decorators'):
                paramdict=sig.parameters
                param_decorators=func.parameter_decorators
        print("THE type is",self.comm_type)
        self.function_schema.update(
            { 'parameters': {'type': 'object','properties': {},'required': []}}
        )
        for param_name, param in paramdict.items():

            if isinstance(param.annotation, str):
                typename = param.annotation  # Treat the string annotation as a regular string
            else:
                typename = param.annotation.__name__  # Access the __name__ attribute of the type object

            oldtypename=typename
            if typename in substitutions:
                typename=substitutions[typename]
            else:
                continue
            param_info = {
                'type': typename,
                'description': param_decorators.get(param_name, '')
            }
            if self.comm_type!='command':
                if typename == '_empty':
                    continue
                if typename == 'Context':
                    continue
            if oldtypename== 'datetime':
                param_info['format']='date-time'
            if oldtypename == 'Literal':
                literal_values = param.annotation.__args__
                param_info['enum'] = literal_values
            self.function_schema['parameters']['properties'][param_name] = param_info
            if param.default == inspect.Parameter.empty or param_name in self.required:
                self.function_schema['parameters']['required'].append(param_name)


    async def invoke_command(self,ctx:Context,function_args:Dict[str,Any]) -> Any:
        '''
        Invokes the LibCommand's associated Discord bot command with the given function arguments.

        Args:

            ctx (Context): The Discord command context.
            function_args (Dict[str, Any]): A dictionary containing the function arguments.

        Returns:

            Any: The outcome of the command execution.

        '''
        bot=ctx.bot
        command=bot.get_command(self.function_name)
        ctx.command=command
        outcome="Done"
        function_args=self.convert_args(function_args)
        if len(function_args)>0:
            for i, v in command.clean_params.items():
                if not i in function_args:
                    print(i,v)
                    function_args[i]=v.default
            ctx.kwargs=(function_args)
        if ctx.command is not None:
            bot.dispatch('command', ctx)
            try:
                if await bot.can_run(ctx, call_once=True):
                    outcome2=await ctx.invoke(command,**function_args)
                    if outcome2!=None:
                        outcome=outcome2
                else:
                    raise CheckFailure('The global check once functions failed.')
            except Exception as exc:
                bot.dispatch('command_error', ctx, exc)
            else:
                bot.dispatch('command_completion', ctx)
        elif ctx.invoked_with:
            exc =  CommandNotFound(f'Command "{self.function_name}" is not found')
            bot.dispatch('command_error', ctx, exc)
        return outcome

class GPTFunctionLibraryDisc(GPTFunctionLibrary):
    """
    A collection of methods to be used with OpenAI's chat completion endpoint.
    When subclassed, decorated methods, called LibCommands, will be added to an internal FunctionDict along with
    a special LibCommand object
    All methods will be converted to a function schema dictionary, which will be sent to OpenAI along with any user text.
    OpenAI will then format paramaters and return them within a JSON object, which will be used to trigger the method
    with call_by_dict.

    This variant was extended to be used with discord.py Bot Commands.

    It's possible to use both subclassed methods and discord.py Bot Commands
    so long as either are decorated with the AILibFunction and LibParam decorators.
    Bot Commands can be defined in any Cog, so long as add_in_commands is called at least once before
    the GPTFunctionLibrary is used with the API.

    Attributes:
        FunctionDict ( Dict[str, Union[Command,callable]]): A dictionary mapping command and method names to the corresponding Command or methods
    """

    FunctionDict: Dict[str, Union[Command,callable]] = {}
    do_expression: bool = False
    my_math_parser:callable=None
    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        """
        Override the __new__ method to update the FunctionDict when instantiating or subclassing.

        Returns:
            The new instance of the class.
        """
        new_cls = super().__new__(cls, *args, **kwargs)
        new_cls._update_function_dict()
        return new_cls

    def add_in_commands(self,bot:Bot) -> None:
        """
        Update the FunctionDict with decorated discord.py bot commands.
        This has to be called somewhere before a call to the AI API if you
        want to use the commands.
        """
        for command in bot.walk_commands():
            print(command.qualified_name)
            if "libcommand" in command.extras:
                print(command.qualified_name, command.extras["libcommand"])
                function_name = command.qualified_name
                self.FunctionDict[function_name] = command.extras["libcommand"]


    async def call_by_dict_ctx(self, ctx:Context, function_dict: Dict[str, Any]) -> Coroutine:
        """
        Call a Coroutine or Bot Command based on the provided dictionary.
        Bot Commands must be decorated.

        Args:
            ctx (commands.Context): context object.
            function_dict (Dict[str, Any]): The dictionary containing the function name and arguments.

        Returns:
            The result of the function call, or Done if there is no returned value.
            This is so something can be added to the bot's message_chain.

        Raises:
            AttributeError: If the function name is not found or not callable.
        """
        try:
            function_name,function_args=self.parse_name_args(function_dict)
        except Exception as e:
            result=str(e)
            return result
        print(function_name, function_args,len(function_args))
        libmethod = self.FunctionDict.get(function_name)
        if libmethod.comm_type=='command':
            return await libmethod.invoke_command(ctx, function_args)

        else:
            if libmethod.comm_type=='coroutine':
                if len(function_args)>0:
                    return await libmethod.command(self,**function_args)
                return await libmethod.command(self)
            elif libmethod.comm_type=='callable':
                if len(function_args)>0:
                    return libmethod.command(self,**function_args)
                return libmethod.command(self)
            else:
                raise AttributeError(f"Method '{function_name}' not found or not callable.")




def LibParam(**kwargs: Any) -> Any:
    """
    Decorator to add descriptions to any valid parameter inside a GPTFunctionLibary method or discord.py bot command.
    AILibFunctions without this decorator will not be sent to the AI.
    Args:
        **kwargs: a function's parameters, and the description to be applied to each.
    Returns:
        The decorated function.
    """
    def decorator(func: Union[Command,callable]) -> callable:
        if isinstance(func,Command):
            print(f"{func} is a command.")
            if not 'parameter_decorators' in func.extras:
                func.extras.setdefault('parameter_decorators',{})
            func.extras['parameter_decorators'].update(kwargs)
            print('new params:',func.extras['parameter_decorators'])
            return func
        else:
            if not hasattr(func, "parameter_decorators"):
                func.parameter_decorators = {}
            func.parameter_decorators.update(kwargs)
            return func
    return decorator

def AILibFunction(name: str, description: str, required:List[str]=[],force_words:List[str]=[], enabled=True) -> Any:
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
    Returns:
        callable, Coroutine, or Command.
    """
    def decorator(func: Union[Command,callable,Coroutine]):
        if isinstance(func, Command):
            #Added to the extras dictionary in the Command
            mycommand=LibCommandDisc(func,name,description,required,force_words,enabled)
            func.extras['libcommand']=mycommand
            return func
        else:
            print("ADDING CALLABLE",func,name)
            mycommand=LibCommandDisc(func,name,description,required,force_words,enabled)
            func.libcommand=mycommand

            return func

    return decorator
