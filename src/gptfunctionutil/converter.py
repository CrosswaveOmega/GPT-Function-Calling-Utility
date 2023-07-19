import inspect
from typing import Any, Dict, List, Optional, Union
from inspect import Parameter

from datetime import datetime



class Converter():
    """
    To convert parameter signatures into extra data.
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
        Convert value into the correct type using the schema Dictionary as a referencean variable of a certain type based on Converter.

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

import re
class BooleanConverter(Converter):
    def to_schema(self, param: inspect.Parameter, dec: Dict[str, Any]) -> Dict[str, Any]:
        schema: Dict[str, Any] = {
            "type": "boolean"
        }


        return schema

    def from_schema(self, value: Any, schema: Dict[str, Any]) -> Optional[str]:

        if not isinstance(value, bool):
            raise ValueError("Value is not of type 'bool'.")

        return value

class StringConverter(Converter):
    def to_schema(self, param: inspect.Parameter, dec: Dict[str, Any]) -> Dict[str, Any]:
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

    def from_schema(self, value: Any, schema: Dict[str, Any]) -> Optional[str]:

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
    def to_schema(self, param: inspect.Parameter, dec: Dict[str, Any]) -> Dict[str, Any]:
        schema=super().to_schema(param,dec)
        schema['format']='datetime'

    def from_schema(self, value: Any, schema: Dict[str, Any]) -> Any:
        value=super().from_schema(value,schema)
        form=schema.get('format',None)
        if not form:
            raise ValueError("No format found.")
        if form=='date-time':
            datetime_format = "%Y-%m-%dT%H:%M:%S%z"
            converted_datetime = datetime.strptime(
                value, datetime_format
                )
            value=converted_datetime
            return value

class NumericConverter(Converter):

    def to_schema(self, param: inspect.Parameter, dec: Dict[str, Any]) -> Dict[str, Any]:
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

    def from_schema(self, value: Any, schema: Dict[str, Any]) -> Any:
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

class NumericConverter(Converter):

    def to_schema(self, param: inspect.Parameter, dec: Dict[str, Any]) -> Dict[str, Any]:
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

    def from_schema(self, value: Any, schema: Dict[str, Any]) -> Any:
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
    def to_schema(self, param: inspect.Parameter, dec: Dict[str, Any]) -> Dict[str, Any]:
        schema: Dict[str, Any] = {
            "type": "array"
        }

        if param.annotation == list:
            schema['items'] = {}  # Empty schema for list validation
        elif param.annotation == tuple:
            prefix_items = []
            for index, item_type in enumerate(param.annotation.__args__):
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
    def to_schema(self, param: inspect.Parameter, dec: Dict[str, Any]) -> Dict[str, Any]:
        schema: Dict[str, Any] = {}
        literal_values = param.annotation.__args__
        schema['type']='string'
        schema['enum'] = literal_values
        schema.update(dec)
        return schema

    def from_schema(self, value: Any, schema: Dict[str, Any]) -> Any:
        if value not in schema['enum']:
            raise ValueError("Value does not match any of the literal values.")
        return value
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
class ConvertStatic():

    @staticmethod
    def parameter_into_schema(param_name:str,param:inspect.Parameter,dec:Union[str,Dict[str,any]]):
        decs=dec
        if isinstance(dec,str):
            decs={'description':dec}
        if isinstance(param.annotation, str):
            typename = param.annotation  # Treat the string annotation as a regular string
        else:
            typename = param.annotation.__name__  # Access the __name__ attribute of the type object


        oldtypename=typename
        if typename in substitutions:
            typename=substitutions[typename]
        else: return None, None
        param_info = {

        }
        if decs.get('description', ''):
            param_info['description']=decs.get('description', '')
        mod=typename().to_schema(param,decs)
        param_info.update(mod)
        return param_info, typename
        if typename in to_ignore:
            return None
        if oldtypename== 'datetime':
            param_info['format']='date-time'
        if oldtypename == 'Literal':
            literal_values = param.annotation.__args__
            param_info['enum'] = literal_values
        return param_info

    @staticmethod
    def schema_validate(param_name:str,value:any,schema:Union[str,Dict[str,any]],converter:Converter):
        typename=None
        if converter!=None:
            typename=converter
        else: return None
        print(typename)
        mod=typename().from_schema(value,schema)
        return mod