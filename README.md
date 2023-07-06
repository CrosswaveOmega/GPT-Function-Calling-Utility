# GPT Function Calling Utility

The GPT Function Calling Utility is a Python package designed to streamline the process of calling Python functions using OpenAI's Function Calling API.

Please note that GPT Function Calling Utility does not directly make calls to OpenAI's API, but rather helps with function modeling and formatting for function invocation.
##Installation
```
python -m pip install -U gptfunctionutil

```
## Key Features

- **Simplified Function Modeling**: The package provides a straightforward way to define and format Python functions to be used with OpenAI's Function Calling API. By subclassing the `GPTFunctionLibrary` class, you can quickly create a set of callable methods to be sent alongwith calls to OpenAi's Chat Completion.

- **Decorate Invokable Functions**: OpenAI's Function Calling api needs a json schema of a functions name, description, and parameters.  This utility uses two decorators, (`@AILibFunction`) and (`@LibParam`) and type annotation to create this schema for functions you want to use with the API.
  + set a display name, description, with (`@AILibFunction`).  You can also specify required parameters with this decorator, but it's not required.
  + apply small descriptions to arguments with (`@LibParam`).
These decorators enable clear documentation and help streamline the function formatting process.

- **Parameter Descriptions and Typing:** To ensure clarity and facilitate proper function formatting, GPT Function Calling Utility requires that all parameters intended to be passed into the AI have an applied type;  strings, integers, floats, and bools.  parameters with a default value are automatically However, the utility is capable of converting some more complex data types to and from a json schema, such as datetimes and Literals, with support for custom converters coming at a later date.

- **Integration with Discord.py**: This utility was intended to be used with life as a discord.py utility, and can be easily integrated with discord.py bots.
   +Simply import gptfunctionutil into your Discord bot project, and decorate your commands with `@LibParam` and `@AILibFunction`.  After passing the Commands into a GPTFunctionLibrary subclass with  `add_in_commands(your_bot_object_here)`, your bot commands will become invokable in the same way as a decorated GPTFunctionLibrary method.

- **Schema Generation for API Calls**: Before making a call to the OpenAI chat/completion endpoint, the utility offers a convenient method, `mylib.get_schema()`, to extract the formatted functions as a list of dictionaries. This schema is then passed as the `functions` field in the API call. If the AI determines that it should invoke a function call, the returned `function_call` dictionary is used with `mylib.call_by_dict(function_call)` to invoke the corresponding function with the provided arguments.

## Usage Example

Using GPT Function Calling Utility with OpenAI to get the current time:

```python

from gptfunctionutil import GPTFunctionLibrary, AILibFunction, LibParam
from datetime import datetime
import openai
class MyLib(GPTFunctionLibrary):
    #Define methods here.
    @AILibFunction(name='get_time', description='Get the current time and day in UTC.')
    @LibParam(comment='An interesting, amusing remark.')
    def get_time(self, comment: str):
        # get the current time, with a small remark.
        return f"{comment}\n{str(datetime.now())}"

# Initialize the subclass somewhere in your code
mylib = MyLib()
completion = openai.ChatCompletion.create(
    model="gpt-3.5-turbo-0613",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        #This message will invoke get_time
        {"role": "user", "content": "Hello, get me the current time in UTC."}
    ],
    functions=mylib.get_schema(),
    function_call="auto"
)
message=completion.choices[0]['message']
if 'function_call' in message:
    result=mylib.call_by_dict(message['function_call'])
    print(result)
else:
    print(completion.choices[0]['message']['content'])
```

