from typing import Literal
from gptfunctionutil import GPTFunctionLibrary, AILibFunction, LibParam
import openai
import asyncio

"""

"""


class MyLib(GPTFunctionLibrary):
    @AILibFunction(name="wait_for", description="Wait for a few seconds, then return.")
    @LibParam(towait="Number of seconds to wait for.")
    async def wait_for(self, towait: int):
        # Wait for a set period of time.
        print(f"launcing waitfor for {towait}.")
        await asyncio.sleep(towait)
        return f"waited for {towait}'!"

    @AILibFunction(
        name="get_current_weather", description="Get the current weather in a given location", required=["location"]
    )
    @LibParam(location="The city and state, e.g. San Francisco, CA")
    async def get_weather(self, location: str, unit: Literal["celsius", "fahrenheit"]):
        # get weather in location.
        print("launcing weather.")
        return f"weather in {location} is {20} degrees {unit}'!"


async def main():
    # Initialize your subclass before calling the API.

    client = openai.AsyncClient()
    mylib = MyLib()

    # Call OpenAI's api
    completion = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Wait for 5 seconds."},
        ],
        tools=mylib.get_tool_schema(),
        tool_choice="auto",
    )
    message = completion.choices[0].message
    if message.tool_calls:
        for tool in message.tool_calls:
            result = await mylib.call_by_tool_async(tool)
            # Print result
            print(result)
    else:
        # Unable to tell that it's a function.
        print(completion.choices[0].message.content)

    completion = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What's the weather like in Boston today?  In C"},
        ],
        tools=mylib.get_tool_schema(),
        tool_choice="auto",
    )
    message = completion.choices[0].message
    if message.tool_calls:
        for tool in message.tool_calls:
            result = await mylib.call_by_tool_async(tool)
            # Print result
            print(result)
    else:
        # Unable to tell that it's a function.
        print(completion.choices[0].message.content)


asyncio.run(main())
