
from __future__ import annotations
from .logger import logs
__version__ = "0.2.2"
import importlib.util
from .converter_core import *
from .convertutil import (
    add_converter,
    ConvertStatic
)
from .errors import *
discord_install = importlib.util.find_spec("discord")
if discord_install is not None:
    try:
        import discord
        logs.info('Importing discord variant.')
        from .functionlib_discord import LibCommandDisc as LibCommand
        from .functionlib_discord import GPTFunctionLibraryDisc as GPTFunctionLibrary
        from .functionlib_discord import AILibFunction
        from .functionlib_discord import LibParam, LibParamSpec
    except ImportError:
        logs.warning('Something went wrong importing discord.')
        from .functionlib import LibCommand as LibCommand
        from .functionlib import GPTFunctionLibrary as GPTFunctionLibrary
        from .functionlib import AILibFunction
        from .functionlib import LibParam, LibParamSpec
else:

    logs.info('Importing core variant.')
    from .functionlib import LibCommand as LibCommand
    from .functionlib import GPTFunctionLibrary as GPTFunctionLibrary
    from .functionlib import AILibFunction
    from .functionlib import LibParam, LibParamSpec
