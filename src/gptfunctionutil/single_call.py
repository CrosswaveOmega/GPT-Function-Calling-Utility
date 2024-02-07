from typing import Any, Dict, List, Optional, Tuple, Union

from .functionlib import GPTFunctionLibrary
from .errors import *
import openai


class SingleCall_Core:
    """
    A class to handle single API calls to a specified model using
    either synchronous or asynchronous client.


    Parameters
    ----------
    mylib : GPTFunctionLibrary
        An instance of GPTFunctionLibrary containing utility functions.
    client : Union[openai.Client, openai.AsyncClient]
        The OpenAI client, which could be either synchronous or asynchronous.
    model : str, optional
        The model to use for the API call. Defaults to "gpt-3.5-turbo-1106".
    systemprompt : str, optional
        The system prompt to use in the API call. Defaults to "You are a helpful assistant.".
    timeout : Optional[float], optional
        The timeout in seconds for the API call. Defaults to None.

    Attributes
    ----------
    model : str
        The model to be used for API calls.
    mylib : GPTFunctionLibrary
        A reference to the GPTFunctionLibrary instance for tool utility functions.
    systemprompt : str
        The system prompt to initialize each call with.
    a_client : openai.AsyncClient, None
        The asynchronous client, if provided.
    client : openai.Client, None
        The synchronous client, if provided.
    timeout : Optional[float]
        The timeout for the API call.

    """

    def __init__(
        self,
        mylib: GPTFunctionLibrary,
        client: Union[openai.Client, openai.AsyncClient],
        model: str = "gpt-3.5-turbo-1106",
        systemprompt: str = "You are a helpful assistant.",
        timeout: Optional[float] = None,
    ):
        self.model = model
        self.mylib = mylib
        self.systemprompt = systemprompt
        self.a_client = self.client = None
        self.timeout = timeout
        if isinstance(client, openai.AsyncClient):
            self.a_client = client
        else:
            self.client = client

    def format_kwargs(self, user_prompt, to_call: Union[str, Dict[str, Dict[str, str]]]) -> Dict[str, Any]:
        """
        Formats the arguments for API call from provided user prompt and tool choice.

        Parameters
        ----------
        user_prompt : str
            The user's input prompt.
        to_call : Union[str, Dict[str, Dict[str, str]]]
            Tool choice either as a string identifier or a dict defining tool and parameters.

        Returns
        -------
        Dict[str, Any]
            A dictionary of the formatted kwargs to be used in an API call.
        """
        callthis = to_call
        if callthis not in ["auto", "none"]:
            callthis = {"type": "function", "function": {"name": to_call}}
        kwargs = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": self.systemprompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            "tools": self.mylib.get_tool_schema(),
            "tool_choice": callthis,
        }
        if self.timeout:
            kwargs["timeout"] = self.timeout
        return kwargs


class SingleCall(SingleCall_Core):
    """
    A class to perform a single synchronous API call to OpenAI and process tool calls within the response.

    This class extends SingleCall_Core to handle synchronous API calls. It is responsible for issuing a single
    call to the OpenAI API, processing the response, and extracting tool calls along with their outputs.

    Parameters
    ----------
    See SingleCall_Core for inherited parameters.

    Methods
    -------
    call_single(user_prompt: str, to_call: str = "auto") -> List[Tuple[str, Any]]:
        Makes a single synchronous call to the OpenAI API with the provided user prompt and optional tool selection,
        returning a list of tuples containing tool names and their outputs.
    """

    def call_single(self, user_prompt: str, to_call: str = "auto") -> List[Tuple[str, Any]]:
        """
        Perform a single synchronous API call to the OpenAI API with a user prompt and an optional tool selection.

        Parameters
        ----------
        user_prompt : str
            The user's input prompt.
        to_call : str, optional
            The tool to call as part of the API request, by default "auto", which automatically selects the tool.

        Returns
        -------
        List[Tuple[str, Any]]
            A list of tuples where each tuple consists of a tool name and its output.

        Raises
        ------
        WrongClient
            Raised if an OpenAI.Client object is not initialized.
        NoToolParams
            Raised if the API response does not contain any valid tool calls.
        """
        kwargs = self.format_kwargs(user_prompt, to_call)
        if self.client is None:
            raise WrongClient("SingleCall requires an OpenAI.Client object. Please correct the initalization.")
        completion = self.client.chat.completions.create(**kwargs)
        message = completion.choices[0].message
        to_return = []
        if message.tool_calls:
            for tool in message.tool_calls:

                function = tool.function
                output = self.mylib.call_by_tool(tool)
                result_tuple = (function, output)
                to_return.append(result_tuple)
            return to_return
        raise NoToolParams("The API did not return any valid tool calls in the response.")


class SingleCallAsync(SingleCall_Core):
    """
    A class for executing asynchronous API calls to OpenAI and processing tool calls within the asynchronous responses.

    This class is an extension of SingleCall_Core specifically designed for asynchronous operation. It issues
    asynchronous API calls to the OpenAI API and processes the responses to extract tool calls and their outputs.

    Parameters
    ----------
    See SingleCall_Core for inherited parameters.

    Methods
    -------
    call_single(user_prompt: str, to_call: str = "auto") -> List[Tuple[str, Any]]:
        Makes a single asynchronous call to the OpenAI API with the provided user prompt and optional tool selection,
        returning a list of tuples containing tool names and their outputs.
    """

    async def call_single(self, user_prompt: str, to_call: str = "auto") -> List[Tuple[str, Any]]:
        """
        Perform a single asynchronous API call to the OpenAI API with a user prompt and an optional tool selection.

        Parameters
        ----------
        user_prompt : str
            The user's input prompt.
        to_call : str, optional
            The tool to call as part of the API request, by default "auto", which automatically selects the tool.

        Returns
        -------
        List[Tuple[str, Any]]
            A list of tuples where each tuple consists of a tool name and its output.

        Raises
        ------
        WrongClient
            Raised if an OpenAI.AsyncClient object is not initialized.
        NoToolParams
            Raised if the API response does not contain any valid tool calls.
        """
        kwargs = self.format_kwargs(user_prompt, to_call)
        if self.a_client is None:
            raise WrongClient(
                "SingleCallAsync requires an OpenAI.AsyncClient object.  Please correct the initalization."
            )
        completion = await self.a_client.chat.completions.create(**kwargs)
        message = completion.choices[0].message
        to_return = []
        if message.tool_calls:
            for tool in message.tool_calls:
                function = tool.function
                output = await self.mylib.call_by_tool_async(tool)
                result_tuple = (function, output)
                to_return.append(result_tuple)
            return to_return
        raise NoToolParams("The API did not return any valid tool calls in the response.")
