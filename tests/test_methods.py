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


import pytest
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


