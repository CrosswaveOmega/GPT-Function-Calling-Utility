from .logger import logs
import inspect
from typing import Any, Dict, List, Optional, Union
from inspect import Parameter
import re
from datetime import datetime
from typing import Type, TypeVar

from .errors import (
    ConversionError,
    ConversionAddError,
    ConversionToError,
    ConversionFromError
)
from .converter_core import *

to_ignore=['_empty','Context']
substitutions={
    'str':StringConverter,
    'int':NumericConverter,
    'bool':BooleanConverter,
    'float':NumericConverter,
    'datetime':DatetimeConverter,
    'Literal':LiteralConverter,
    'List':ArrayConverter
}
def add_converter(fortype: Type, converterclass: Type[Converter]) -> None:
    '''
    Add a new converter that will generate schema for Objects of Class fortype, and
    initalize new instances of fortype on validation.

    Parameters:
        fortype (Type): The Class the converter will creates schema for and create new
        instances of on validation
        converterclass (Type[Converter]): The class descended from Converter.

    Raises:
        ConversionAddError: If the type already exists in the dictionary.

    Returns:
        None
    '''
    typename = fortype.__name__  # Access the name attribute of the type object

    if typename not in substitutions:
        substitutions[typename] = converterclass
        logs.info(f"Adding converterclass %s for type %s",typename,converterclass)
    else:
        raise ConversionAddError(f'{typename} already in dictionary!')
class ConvertStatic():
    '''static class for to_schema and from_schema logic.'''
    @staticmethod
    def parameter_into_schema(param_name:str,param:inspect.Parameter,dec:Union[str,Dict[str,any]])->Tuple[Dict[str, any], Type[Converter]]:
        """
        Generate a schema for the Converts a parameter signature into a schema.

        Parameters:
        param_name (str): The name of the parameter.
        param (inspect.Parameter): The parameter signature to convert .
        dec (Union[str, Dict[str, any]]): Additional keywords to be added to the schema,
        including definition

        Returns:
        Tuple[Dict[str, any], Type[Converter]]: The schema generated along with the Converter Class.

        Raises:
        ConversionToError: If conversion to schema fails.
        """
        decs=dec
        if isinstance(dec,str):
            decs={'description':dec}
        if isinstance(param.annotation, str):
            typename = param.annotation  # Treat the string annotation as a regular string
        else:
            typename = param.annotation.__name__  # Access the __name__ attribute of the type object


        oldtypename=typename
        converter=None
        if typename in substitutions:
            converter=substitutions[typename]
        else:
            logs.info(f"type %s was not found!",typename)
            return None, None
        param_info = {}
        if decs.get('description', ''):
            param_info['description']=decs.get('description', '')
        mod=converter().to_schema(param,decs)
        if mod==None:
            raise ConversionToError(param_name,param,dec)
        param_info.update(mod)
        logs.info(f"schema generated for param %s with type %s!",param_name,typename)
        return param_info, converter


    @staticmethod
    def schema_validate(param_name:str,value:any,schema:Union[str,Dict[str,any]],converter:Converter)->Any:
        """
        Validate and apply needed a value based on schema.

        Parameters:
        param_name (str): The name of the parameter.
        value (any): The value to validate.
        schema (Union[str, Dict[str, any]]): The schema to validate against.
        converter (Converter): The converter to use for validation.

        Returns:
        any: The validated value.

        Raises:
        ConversionFromError: If conversion from schema fails.
        """
        ...
        typename=None
        if converter!=None:
            typename=converter
        else:
            error=ConversionFromError(param_name,value,schema,msg='No converter found.')
            logs.error(error, exc_info=1,stack_info=True)
            raise error
        try:
            mod=typename().from_schema(value,schema)
        except Exception as e:
            try:
                raise ConversionFromError(param_name,value,schema,str(e)) from e
            except Exception as e:
                logs.error(e, exc_info=1,stack_info=True)
                raise e
        return mod