from .logger import logs
import inspect
from typing import Any, Dict, List, Optional, Tuple, Union
from inspect import Parameter
import re
from datetime import datetime

from .errors import (
    ConversionError,
    ConversionAddError,
    ConversionToError,
    ConversionFromError
)
class Converter():
    """
    To convert parameter signatures into a JSON Schema friendly representaion, and to
    convert/verify in return.
    """

    def to_schema(self, param:inspect.Parameter,dec:Dict[str,Any])->Dict[str,Any]:
        """
        Generate a schema from a parameter signature.

        Parameters
        -----------
        param: :class:`inspect.Parameter`
            The Parameter signature to convert
        dec: :class:`Dict[str,any]`
            Dictionary of additional attributes to be considered.
        Returns
        ------
            Dict[str,any]
        Raises
        -------
        """
        raise NotImplementedError('Derived classes need to implement this.')
    def from_schema(self,value:Any,schema:Dict[str,Any])->Any:
        """
        Convert value into the correct type using the schema Dictionary as a reference.
        More important for more complex objects.


        Parameters
        -----------
        value: :class: `Any`
            a variable to be converted based on the schema Dict
        schema: :class:`Dict[str,Any]`
            The schema that value should follow.
        Returns
        --------
        New instance of the class/type the converter is for.
        Raises
        -------
        """
        raise NotImplementedError('Derived classes need to implement this.')


class BooleanConverter(Converter):
    """
    This converter is for Boolean values.
    """
    def to_schema(self, param: inspect.Parameter, dec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a boolean type schema from a parameter signature.

        Parameters
        -----------
        param: :class:`inspect.Parameter`
            The Parameter signature to convert.  Should have a string type annotation.
        dec: :class:`Dict[str,Any]`
            Dictionary of additional attributes to be added to the schema.
        Returns
        ------
            Dict[str,Any]: the schema generated for param
        Raises
        -------
        """
        schema: Dict[str, Any] = {
            "type": "boolean"
        }
        return schema

    def from_schema(self, value: Any, schema: Dict[str, Any]) -> bool:

        if not isinstance(value, bool):
            raise ValueError("Value is not of type 'bool'.")

        return value

class StringConverter(Converter):
    '''This converter is for string types, as well as custom types that can be derived from strings,
        such as datetimes.'''
    def to_schema(self, param: inspect.Parameter, dec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a schema (for a string type) from a parameter signature and declare additonal keywords.

        Parameters
        -----------
        param: :class:`inspect.Parameter`
            The Parameter signature to convert.  Should have a str annotation.
        dec: :class:`Dict[str,Any]`
            Dictionary of additional attributes to be added to the schema.
            valid keywords include minLength, maxLength, and pattern
        Returns
        ------
            Dict[str,Any]: the schema generated for param.
        Raises
        -------
        """
        schema: Dict[str, Any] = {
            "type": "string"
        }

        # Check for length constraints
        if 'minLength' in dec or param.default is None:
            schema['minLength'] = dec.get('minLength', 0)
        if 'maxLength' in dec or param.default is None:
            schema['maxLength'] = dec.get('maxLength', 255)

        # Check for pattern constraint
        if 'pattern' in dec:
            schema['pattern'] = dec['pattern']

        return schema

    def from_schema(self, value: Any, schema: Dict[str, Any]) -> str:
        """
        Validate and return string value.

        Parameters
        -----------
        value: :class: `Any`
            a variable to be validated with the schema Dict
        schema: :class:`Dict[str,Any]`
            The schema that value will be validated with follow.
        Returns
        --------
            `str`: value if validation was successfull.
        Raises
        -------
        ValueError- if Validation has failed
        """
        if not isinstance(value, str):
            raise ValueError("Value is not of type 'str'.")

        if 'minLength' in schema and len(value) < schema['minLength']:
            raise ValueError("Value does not meet the minLength constraint.")

        if 'maxLength' in schema and len(value) > schema['maxLength']:
            raise ValueError("Value exceeds the maxLength constraint.")

        if 'pattern' in schema and not re.match(schema['pattern'], value):
            raise ValueError("Value does not match the specified pattern.")

        return value
class DatetimeConverter(StringConverter):
    '''This converter is for datetime objects, which are derived from a string.'''
    def to_schema(self, param: inspect.Parameter, dec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a string type schema, and then apply a 'date-time' format.
        This will force OpenAI to return a formatted string with the function call
        which is used to initalize a new datetime.

        Parameters
        -----------
        param: :class:`inspect.Parameter`
            The Parameter signature to convert.  Should have a datetime annotation.
        dec: :class:`Dict[str,Any]`
            Dictionary of additional attributes to be added to the schema.
        Returns
        ------
            `Dict[str,Any]`: the schema generated for param.
        Raises
        -------
        """
        schema=super().to_schema(param,dec)
        schema['format']='date-time'
        return schema

    def from_schema(self, value: str, schema: Dict[str, Any]) -> datetime:
        """
        Validate string value and initalize a datetime object.

        Parameters
        -----------
        value: :class: `str`
            a variable to be validated with the schema Dict
        schema: :class:`Dict[str,Any]`
            The schema that value will be validated with follow.
        Returns
        --------
            `datetime`: A new datetime derived from value.
        Raises
        -------
        ValueError- if Validation has failed or the format keyword is missing/not set to date-time in schema.
        """
        value=super().from_schema(value,schema)
        form=schema.get('format',None)
        if not form:
            raise ValueError("No format found.")
        if form=='date-time':
            datetime_format = "%Y-%m-%dT%H:%M:%S%z"
            converted_datetime = datetime.strptime(
                value, datetime_format
                )
            newvalue=converted_datetime
            return newvalue
        else:
            raise ValueError('Format is not "date-time" ')

class NumericConverter(Converter):

    '''This Converter is for floats and integers'''
    def to_schema(self, param: inspect.Parameter, dec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a number or integer type schema from a parameter signature and declare additonal keywords.

        Parameters
        -----------
        param: :class:`inspect.Parameter`
            The Parameter signature to convert.  Should have an `int` or `float` annotation.
        dec: :class:`Dict[str,Any]`
            Dictionary of additional attributes to be added to the schema.

        Returns
        ------
            `Dict[str,Any]`: the schema generated for param.
        Raises
        -------
        """
        schema: Dict[str, Any] = {}

        if 'minimum' in dec:
            schema['minimum'] = dec['minimum']
        if 'maximum' in dec:
            schema['maximum'] = dec['maximum']
        if 'exclusiveMinimum' in dec:
            schema['exclusiveMinimum'] = dec['exclusiveMinimum']
        if 'exclusiveMaximum' in dec:
            schema['exclusiveMaximum'] = dec['exclusiveMaximum']
        if 'multipleOf' in dec:
            schema['multipleOf'] = dec['multipleOf']

        if param.annotation == int:
            schema['type'] = 'integer'
        else:
            schema['type'] = 'number'

        return schema

    def from_schema(self, value: Any, schema: Dict[str, Any]) -> Union[float, int]:
        """
        Ensure that value is an integer or float, and validate with schema.

        Parameters
        -----------
        value: :class: `Any`
            a variable to be validated
        schema: :class:`Dict[str,Any]`
            The schema that value will be validated with follow.
        Returns
        --------
            `Union[float, int]`: validated float or integer value.
        Raises
        -------
        ValueError- if Validation has failed or the format keyword is missing/not set to date-time in schema.
        """
        if not isinstance(value, (int, float)):
            raise ValueError("Value is not of type 'int' or 'float'.")

        if 'minimum' in schema and value < schema['minimum']:
            raise ValueError("Value is below the minimum constraint.")

        if 'maximum' in schema and value > schema['maximum']:
            raise ValueError("Value exceeds the maximum constraint.")

        if 'exclusiveMinimum' in schema and value <= schema['exclusiveMinimum']:
            raise ValueError("Value does not meet the exclusiveMinimum constraint.")

        if 'exclusiveMaximum' in schema and value >= schema['exclusiveMaximum']:
            raise ValueError("Value does not meet the exclusiveMaximum constraint.")

        if 'multipleOf' in schema and value % schema['multipleOf'] != 0:
            raise ValueError("Value does not meet the multipleOf constraint.")

        return value


class ArrayConverter(Converter):
    '''This Converter is for Arrays.  Currenly unstable.'''
    def to_schema(self, param: inspect.Parameter, dec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate an array schema for a List or Tuple.


        Parameters
        -----------
        param: :class:`inspect.Parameter`
            The Parameter signature to convert.  Should have a List or Tuple annotation with defined
            element typing for an integers, floats, string, or boolean
        dec: :class:`Dict[str,Any]`
            Dictionary of additional attributes to be added to the schema.

        Returns
        ------
            `Dict[str,Any]`: the schema generated for param.
        Raises
        -------
        """
        schema: Dict[str, Any] = {
            "type": "array"
        }
        if param.annotation == list or getattr(param.annotation, "__origin__", None) == list:
            # Check if the annotation is 'list' or an instance of the 'List' type hint from typing module
            schema['items']={}
            element_type = getattr(param.annotation, "__args__", [Any])[0]
            schema['items']= self._get_type_schema(element_type)

        elif param.annotation == Tuple or getattr(param.annotation, "__origin__", None) == Tuple:
            prefix_items = []
            for item_type in getattr(param.annotation, "__args__", [Any]):
                prefix_items.append(self._get_type_schema(item_type))
            schema['prefixItems'] = prefix_items


        # Length constraints
        if 'minItems' in dec:
            schema['minItems'] = dec['minItems']
        if 'maxItems' in dec:
            schema['maxItems'] = dec['maxItems']

        # Uniqueness constraint
        if 'uniqueItems' in dec:
            schema['uniqueItems'] = dec['uniqueItems']

        return schema

    def from_schema(self, value: Any, schema: Dict[str, Any]) -> List:
        """
        Validate if value is a valid array based on schema.

        Parameters
        -----------
        value: :class: `Any`
            a variable to be validated.  Should be a list
        schema: :class:`Dict[str,Any]`
            The schema that value will be validated with follow.
        Returns
        --------
        List->
        Raises
        -------
        ValueError- if Validation has failed or the format keyword is missing/not set to date-time in schema.
        """
        if not isinstance(value, list):
            raise ValueError("Value is not of type 'list'.")

        if 'minItems' in schema and len(value) < schema['minItems']:
            raise ValueError("Value does not meet the minItems constraint.")

        if 'maxItems' in schema and len(value) > schema['maxItems']:
            raise ValueError("Value exceeds the maxItems constraint.")

        if 'uniqueItems' in schema and schema['uniqueItems'] is True:
            if len(set(value)) != len(value):
                raise ValueError("Value does not meet the uniqueItems constraint.")

        return value

    def _get_type_schema(self, item_type: type) -> Dict[str, Any]:
        if item_type == int:
            return {"type": "integer"}
        elif item_type == float:
            return {"type": "number"}
        elif item_type == str:
            return {"type": "string"}
        elif item_type == bool:
            return {"type": "boolean"}
        else:
            return {}  # Empty schema for custom types

class LiteralConverter(Converter):
    '''Create enums from literals, eg Literal['a','b,'c'].
    Currently, only String Literals can be used..'''
    def to_schema(self, param: inspect.Parameter, dec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate an enum schema for a passed in Literal annotated parameter schema.


        Parameters
        -----------
        param: :class:`inspect.Parameter`
            The Parameter signature to convert.  Should have a Literal annotation.
            Currently, only s
        dec: :class:`Dict[str,Any]`
            Dictionary of additional attributes to be added to the schema.

        Returns
        ------
            `Dict[str,Any]`: the schema generated for param.
        Raises
        -------
        """
        schema: Dict[str, Any] = {}
        literal_values = param.annotation.__args__
        schema['type']='string'
        schema['enum'] = literal_values
        schema.update(dec)
        return schema

    def from_schema(self, value: Any, schema: Dict[str, Any]) -> Any:
        """
        Validate by ensuring if value is within schema's 'enum' field

        Parameters
        -----------
        value: :class: `Any`
            a variable to be validated.
        schema: :class:`Dict[str,Any]`
            The schema that value will be validated with.
        Returns
        --------
            value `str`->value
        Raises
        -------
        ValueError- if Validation has failed or the format keyword is missing/not set to date-time in schema.
        """
        if value not in schema['enum']:
            raise ValueError(f"Value {value} does not match any of the literal values.")
        return value