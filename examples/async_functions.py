
import inspect
import re
from typing import Any, Dict
from gptfunctionutil import GPTFunctionLibrary, AILibFunction, LibParam
from gptfunctionutil import add_converter,StringConverter
from datetime import datetime
import openai
import asyncio


class MyLib(GPTFunctionLibrary):
    @AILibFunction(name='wait_for',description='Wait for a few seconds, then return.')
    @LibParam(targetuser='Number of seconds to wait for.')
    async def wait_for(self,towait:int):
        #Nothing fancy.  Just get the id, the type, and the string representation of User.
        print('launcing waitfor.')
        await asyncio.sleep(towait)
        return f"waited for {towait}'!"


async def main():
    # Initialize your subclass before calling the API.
    mylib = MyLib()

    #Call OpenAI's api
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Wait for 25 seconds."}
        ],
        functions=mylib.get_schema(),
        function_call="auto"
    )
    message=completion.choices[0]['message']
    if 'function_call' in message:
        #Process function call.
        result=await mylib.call_by_dict_async(message['function_call'])
        #Print result
        print(result)
    else:
        #Unable to tell that it's a function.
        print(completion.choices[0]['message']['content'])


asyncio.run(main())