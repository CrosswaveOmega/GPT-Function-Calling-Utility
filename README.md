# GPT Function Calling Utility

The GPT Function Calling Utility is a Python package designed to streamline the process of calling Python methods using OpenAI's Function Calling API, without wrapping around the OpenAI library.

Please note that GPT Function Calling Utility does not directly make calls to OpenAI's API, but rather helps with function modeling and formatting for function invocation.

##Installation
```
python -m pip install -U gptfunctionutil

```
## Key Features

- **Simplified Function Modeling Via Inheritance**: This package utilizes subclasses decended from the `GPTFunctionLibrary` class that allows you to define sets of callable methods to be sent to OpenAI's Chat Completion endpoint.  `GPTFunctionLibrary` contains methods to create a json schema describing your defined methods, and has methods that invoke methods utilizing the Function Call field returned with a call to chat/completions.

- **Decorate Invokable Functions**: OpenAI's Function Calling Feature needs a JSON object of every single function's name, description, and parameters.  This utility uses two decorators, (`@AILibFunction`) and (`@LibParam`), as well as type annotation to create this schema for functions you want to use with the API.
  + set a display name and description with (`@AILibFunction`).  You can also specify required parameters with this decorator, but it's not required.
  + apply small descriptions to arguments with (`@LibParam`), to inform the API on what it does.
  + (`@LibParamSpec`) can apply additional keywords depending on the type. (see https://json-schema.org/understanding-json-schema/index.html for details.)


- **Parameter Typing and Descriptions:** To ensure clarity and facilitate proper function formatting, GPT Function Calling Utility requires that all parameters intended to be passed into the AI have an applied type;  strings, integers, floats, and bools.  The library utilizes a collection of converter objects to generate schema for each parameter based on type annotations.

- **Convert into complex types:** The utility is capable of converting some more complex data types into a json schema, such as datetimes and Literals.
   + Define Custom Converters to automatically use response arguments to initalize objects.
     +  (see examples/custom_converters.py for an example.)

- **Integration with Discord.py**: This utility was intended to be used with life as a discord.py utility, and can be easily integrated with discord.py bots.
   + Simply import `gptfunctionutil` into your Discord bot project, and decorate your commands with `@LibParam` and `@AILibFunction`.  After passing the Commands into a GPTFunctionLibrary subclass with  `add_in_commands(your_bot_object_here)`, your bot commands will become invokable in the same way as a decorated GPTFunctionLibrary method.

- **Schema Generation for API Calls**: Before making a call to the OpenAI chat/completion endpoint, the utility has a `get_schema()` method to extract the formatted functions as a list of dictionaries. This schema is then passed as the `functions` field in the ChatCompletion call. If the AI determines that it should invoke a function call, the returned `function_call` dictionary is used with `call_by_dict(function_call)`(or `call_by_dict_ctx` if decorating a discord.py command.) to invoke the corresponding function with the provided arguments.
   + The method also checks if there is a function by that name, falling back to a default response if something goes wrong.
   + Schema can also validate and convert responces returned from the chat/completions endpoint.

## Usage Example

Using GPT Function Calling Utility with OpenAI to get the current time:

```python

from gptfunctionutil import GPTFunctionLibrary, AILibFunction, LibParam, LibParamSpec
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

