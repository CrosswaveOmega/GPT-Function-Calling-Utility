
from __future__ import annotations

__version__ = "0.1.7"
import importlib.util
from .converter import *
from .errors import *
discord_install = importlib.util.find_spec("discord")
if discord_install is not None:
    try:
        import discord
        from .functionlib_discord import LibCommandDisc as LibCommand
        from .functionlib_discord import GPTFunctionLibraryDisc as GPTFunctionLibrary
        from .functionlib_discord import AILibFunction
        from .functionlib_discord import LibParam
    except ImportError:
        print('Something went wrong importing discord')
        from .functionlib import LibCommand as LibCommand
        from .functionlib import GPTFunctionLibrary as GPTFunctionLibrary
        from .functionlib import AILibFunction
        from .functionlib import LibParam, LibParamSpec
else:
    from .functionlib import LibCommand as LibCommand
    from .functionlib import GPTFunctionLibrary as GPTFunctionLibrary
    from .functionlib import AILibFunction
    from .functionlib import LibParam, LibParamSpec
