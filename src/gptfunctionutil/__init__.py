from __future__ import annotations
from .logger import logs

__version__ = "0.3.7.2"
import importlib.util
from .converter_core import *
from .convertutil import add_converter, ConvertStatic
from .errors import *
from .functionlib import LibParam, LibParamSpec

discord_install = importlib.util.find_spec("discord")
if discord_install is not None:
    try:
        import discord

        logs.info("Importing discord variant.")
        from .functionlib_discord import (
            LibCommandDisc as LibCommand,
            GPTFunctionLibraryDisc as GPTFunctionLibrary,
            AILibFunction,
        )
    except ImportError:
        logs.warning("Something went wrong importing discord.")
        from .functionlib import LibCommand, GPTFunctionLibrary, AILibFunction
else:
    logs.info("Importing core variant.")
    from .functionlib import LibCommand, GPTFunctionLibrary, AILibFunction

from .single_call import SingleCall, SingleCallAsync
