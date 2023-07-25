#   ---------------------------------------------------------------------------------
#   Copyright (c) Microsoft Corporation. All rights reserved.
#   Licensed under the MIT License. See LICENSE in project root for information.
#   ---------------------------------------------------------------------------------
"""This is a sample python file for testing functions from the source code."""
from __future__ import annotations

from gptfunctionutil import *


import pytest
@pytest.mark.asyncio
async def test_command_function_load():
    class MyTestLib(GPTFunctionLibrary):
        @AILibFunction(name='get_time',description='Get the current time and day in UTC.')
        @LibParam(comment='An interesting, amusing remark.')
        def get_time(self,comment:str):
            #This is an example of a decorated coroutine command.
            return f"{comment}"
    #pass
    testlib=MyTestLib()
    schema = testlib.get_schema()
    assert 'name' in schema[0]
    assert schema[0]['name'] == 'get_time'

    result=testlib.call_by_dict({'name':'get_time','arguments':"{\"comment\":\"This is an interesting, amusing remark.\"}"})
    assert result == "This is an interesting, amusing remark."


@pytest.mark.asyncio
async def test_command_function_errorsload():
    class MyTestLib(GPTFunctionLibrary):
        @AILibFunction(name='get_time',description='Get the current time and day in UTC.')
        @LibParam(comment='An interesting, amusing remark.')
        def get_time(self,comment:str):
            #This is an example of a decorated coroutine command.
            return f"{comment}"
    #pass
    testlib=MyTestLib()
    schema = testlib.get_schema()
    assert 'name' in schema[0]
    assert schema[0]['name'] == 'get_time'

    result=testlib.call_by_dict({'name':'notafunction','arguments':"{\"comment\":\"This is an interesting, amusing remark.\"}"})
    assert 'is not a valid function' in result

import inspect
from typing import Any, Dict, List, Optional, Union
from inspect import Parameter
import re
@pytest.mark.asyncio
async def test_advanced_objects():
    class MyTestLib2(GPTFunctionLibrary):
        @AILibFunction(name='get_time',description='Get the current time and day in UTC.')
        @LibParam(comment='An interesting, amusing remark.')
        def get_time(self,comment:str):
            #This is an example of a decorated coroutine command.
            return f"{comment}"
        @AILibFunction(name='set_alarm',description='Set an alarm.')
        @LibParam(alarm_time='Datetime to set this alarm at.')
        def set_alarm(self,alarm_time:datetime):
            #This is an example of a decorated coroutine command.
            result=f"{str(alarm_time.date())}"
            print(result)
            return result
    #pass
    testlib2=MyTestLib2()
    schema = testlib2.get_schema()
    print(schema)
    assert 'name' in schema[0]
    assert schema[1]['name'] == 'set_alarm'

    result=testlib2.call_by_dict({'name':'set_alarm','arguments':"{\"alarm_time\":\"2018-11-13T20:20:39+00:00\"}"})
    assert result == "2018-11-13"


@pytest.mark.asyncio
async def test_string_converter_to_schema():
    converter = StringConverter()
    param = inspect.Parameter('param', Parameter.POSITIONAL_OR_KEYWORD)
    dec = {'minLength': 5, 'maxLength': 10, 'pattern': r'^[a-zA-Z]+$'}
    expected_schema = {'type': 'string', 'minLength': 5, 'maxLength': 10, 'pattern': r'^[a-zA-Z]+$'}
    assert converter.to_schema(param, dec) == expected_schema

@pytest.mark.asyncio
async def test_string_converter_from_schema():
    converter = StringConverter()
    value = 'test'
    schema = {'type': 'string', 'minLength': 3, 'maxLength': 5, 'pattern': r'^[a-z]+$'}
    expected_result = 'test'
    assert converter.from_schema(value, schema) == expected_result

@pytest.mark.asyncio
async def test_string_converter_from_schema_with_invalid_value():
    converter = StringConverter()
    value = 123
    schema = {'type': 'string'}
    with pytest.raises(ValueError):
        converter.from_schema(value, schema)


@pytest.mark.asyncio
async def test_numeric_converter_to_schema():
    converter = NumericConverter()
    param = inspect.Parameter('param', Parameter.POSITIONAL_OR_KEYWORD, annotation=int)

    # Test case with minimum and maximum constraints only
    dec1 = {'minimum': 0, 'maximum': 10}
    expected_schema1 = {'type': 'integer', 'minimum': 0, 'maximum': 10}
    assert converter.to_schema(param, dec1) == expected_schema1

    # Test case with exclusive minimum and exclusive maximum constraints only
    dec2 = {'exclusiveMinimum': 0, 'exclusiveMaximum': 10}
    expected_schema2 = {'type': 'integer', 'exclusiveMinimum': 0, 'exclusiveMaximum': 10}
    assert converter.to_schema(param, dec2) == expected_schema2

    # Test case with multipleOf constraint only
    dec3 = {'multipleOf': 2}
    expected_schema3 = {'type': 'integer', 'multipleOf': 2}
    assert converter.to_schema(param, dec3) == expected_schema3

    # Test case with all constraints
    dec4 = {'minimum': 0, 'maximum': 10, 'exclusiveMinimum': 0, 'exclusiveMaximum': 10, 'multipleOf': 2}
    expected_schema4 = {'type': 'integer', 'minimum': 0, 'maximum': 10, 'exclusiveMinimum': 0, 'exclusiveMaximum': 10, 'multipleOf': 2}
    assert converter.to_schema(param, dec4) == expected_schema4

    # Test case with no constraints
    dec5 = {}
    expected_schema5 = {'type': 'integer'}
    assert converter.to_schema(param, dec5) == expected_schema5


@pytest.mark.asyncio
async def test_numeric_converter_from_schema():
    converter = NumericConverter()
    value = 5
    schema = {'type': 'integer', 'minimum': 0, 'maximum': 10, 'exclusiveMinimum': -1, 'exclusiveMaximum': 11, 'multipleOf': 5}
    expected_result = 5
    assert converter.from_schema(value, schema) == expected_result

@pytest.mark.asyncio
async def test_numeric_converter_from_schema_with_invalid_value():
    converter = NumericConverter()
    value = 'test'
    schema = {'type': 'integer'}
    with pytest.raises(ValueError):
        converter.from_schema(value, schema)

@pytest.mark.asyncio
async def test_numeric_converter_from_schema_below_minimum():
    converter = NumericConverter()
    value = -1
    schema = {'type': 'integer', 'minimum': 0}
    with pytest.raises(ValueError):
        converter.from_schema(value, schema)

@pytest.mark.asyncio
async def test_numeric_converter_from_schema_above_maximum():
    converter = NumericConverter()
    value = 15
    schema = {'type': 'integer', 'maximum': 10}
    with pytest.raises(ValueError):
        converter.from_schema(value, schema)

@pytest.mark.asyncio
async def test_numeric_converter_from_schema_below_exclusive_minimum():
    converter = NumericConverter()
    value = -1
    schema = {'type': 'integer', 'exclusiveMinimum': 0}
    with pytest.raises(ValueError):
        converter.from_schema(value, schema)

@pytest.mark.asyncio
async def test_numeric_converter_from_schema_above_exclusive_maximum():
    converter = NumericConverter()
    value = 11
    schema = {'type': 'integer', 'exclusiveMaximum': 10}
    with pytest.raises(ValueError):
        converter.from_schema(value, schema)

@pytest.mark.asyncio
async def test_numeric_converter_from_schema_not_multiple_of():
    converter = NumericConverter()
    value = 7
    schema = {'type': 'integer', 'multipleOf': 3}
    with pytest.raises(ValueError):
        converter.from_schema(value, schema)

@pytest.mark.asyncio
async def test_array_converter_to_schema():
    converter = ArrayConverter()
    param = inspect.Parameter('param', Parameter.POSITIONAL_OR_KEYWORD, annotation=List[str])
    dec = {'minItems': 1, 'maxItems': 5, 'uniqueItems': True}
    expected_schema = {'type': 'array', 'items': {"type":'string'}, 'minItems': 1, 'maxItems': 5, 'uniqueItems': True}
    schema=converter.to_schema(param, dec)
    print(schema)
    assert schema== expected_schema

@pytest.mark.asyncio
async def test_array_converter_from_schema_with_invalid_value():
    converter = ArrayConverter()
    value = 'test'
    schema = {'type': 'array'}
    with pytest.raises(ValueError):
        converter.from_schema(value, schema)

@pytest.mark.asyncio
async def test_check_converter():
    class User:
        def __init__(self, user):
            self.user = user

        def __str__(self):
            return str(self.user)

        def __repr__(self):
            return str(self.user)
    class UserConverter(StringConverter):
        def to_schema(self, param: inspect.Parameter, dec: Dict[str, Any]) -> Dict[str, Any]:
            schema=super().to_schema(param,dec)
            schema['pattern']= r'<@!?(\d+)>'
            return schema

        def from_schema(self, value: Any, schema: Dict[str, Any]) -> Any:
            value=super().from_schema(value,schema)
            pat=schema.get('pattern',None)
            if not pat:
                raise ValueError("No pattern found.")
            print(pat)
            extract=re.match(pat,value)[1]
            return extract
    add_converter(User,UserConverter)
    class MyTestLib6(GPTFunctionLibrary):
        @AILibFunction(name='get_user',description='Get a specific user id')
        @LibParam(targetuser='The user to retrieve')
        def get_user(self,targetuser:User):
            #This is an example of a decorated coroutine command.
            return f"{targetuser}"

    testlib3=MyTestLib6()
    schema = testlib3.get_schema()
    print(schema)


    result=testlib3.call_by_dict({'name':'get_user','arguments':"{\"targetuser\":\"<@1234567890>\"}"})
    assert result == "1234567890"

