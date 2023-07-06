#   ---------------------------------------------------------------------------------
#   Copyright (c) Microsoft Corporation. All rights reserved.
#   Licensed under the MIT License. See LICENSE in project root for information.
#   ---------------------------------------------------------------------------------
"""This is a sample python file for testing functions from the source code."""
from __future__ import annotations

from gptfunctionutil.functionlib import *



import pytest
from discord.ext import commands
import discord
# Define a dummy cog for testing
class TestCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    @AILibFunction(name='test_command',description='this is a test command')
    @LibParam(powe=str)
    @commands.command()
    async def test_command(self, ctx, powe:str):
        await ctx.send("Test command executed!")
    @commands.command()
    async def noninvoke_test_command(self, ctx, powe:str):
        await ctx.send("Test command executed!")


# Define the pytest fixture for the Bot
@pytest.fixture(scope='session')
async def bot():
    bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
    await bot.add_cog(TestCog(bot))
    #await bot.start('YOUR_BOT_TOKEN')  # Replace with your bot token
    yield bot
    await bot.close()

# Test to ensure all commands are registered
@pytest.mark.asyncio
async def test_command_registration(bot):
    async for bot in bot:
        registered_commands = []
        for command in bot.walk_commands():
            registered_commands.append(command.name)
        assert 'test_command' in registered_commands
        assert 'noninvoke_test_command' in registered_commands
# Test to ensure all commands are registered


@pytest.mark.asyncio
async def test_command_function_load(bot):
    class MyTestLib(GPTFunctionLibrary):
        @AILibFunction(name='get_time',description='Get the current time and day in UTC.')
        @LibParam(comment='An interesting, amusing remark.')
        async def get_time(self,comment:str):
            #This is an example of a decorated coroutine command.
            return f"{comment}\n{str(discord.utils.utcnow())}"
    #pass
    testlib=MyTestLib()
    async for bot in bot:
        schema = testlib.get_schema()
        assert 'get_time' in schema
        testlib.add_in_commands(bot)
        registered_commands = []
        for command in bot.walk_commands():
            registered_commands.append(command.name)
        assert 'test_command' in registered_commands
        assert 'test_command' in schema
        assert 'noninvoke_test_command' in registered_commands



# Example usage of the bot fixture
@pytest.mark.asyncio
async def test_bot(bot):
    async for bot in bot:
        assert bot is not None
        assert isinstance(bot, commands.Bot)