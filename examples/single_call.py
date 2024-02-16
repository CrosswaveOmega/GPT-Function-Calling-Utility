from typing import List
from gptfunctionutil import SingleCall
from openai import Client
from gptfunctionutil import GPTFunctionLibrary, AILibFunction, LibParam, LibParamSpec
import asyncio


"""Example of the single call utility function along with the use of LibParamSpec for an array."""


class MyCall(GPTFunctionLibrary):

    @AILibFunction(
        name="followupquestions",
        description="Create a list of follow up questions to expand on a query.",
        required=["followup"],
    )
    @LibParamSpec(name="followup", description="A list of followup questions.", minItems=3, maxItems=10)
    def followup_questions(self, followup: List[str]):
        # Wait for a set period of time.
        print("foll:", followup)

        return followup


def make_query():
    client = Client()
    sc = SingleCall(mylib=MyCall(), client=client)

    command = sc.call_single(
        'Generate 5 followup questions for "What jellyfish species are mostly found in the deep sea?"',
        "followupquestions",
    )
    print(command)


make_query()
