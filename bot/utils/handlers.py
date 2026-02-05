import importlib
import pkgutil

from aiogram.filters import Command

import bot.commands
from bot.messages.messages import register_message_handlers
from bot.modules.buttons import register_button_handlers
from bot.utils.command_registry import COMMAND_REGISTRY


def register_handlers(dp):
    """Регистрирует все обработчики бота."""
    for module in pkgutil.iter_modules(bot.commands.__path__):
        importlib.import_module(f"bot.commands.{module.name}")

    for entry in COMMAND_REGISTRY:
        router = entry.get("router")
        if router:
            dp.include_router(router)
        else:
            dp.message.register(entry["handler"], Command(commands=[entry["name"]]))
    register_button_handlers(dp)
    register_message_handlers(dp)
