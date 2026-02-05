import inspect
import logging
from typing import Any, Callable, Dict, List, Optional

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

COMMAND_REGISTRY: List[Dict[str, Any]] = []


def command(
    name: str,
    flag: bool = True,
    *,
    router: Optional[Router] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Декоратор для регистрации команд.

    Args:
        name: Имя команды без слеша.
        flag: Флаг доступности команды.
        router: Опциональный Router для регистрации обработчика.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        async def wrapper(message: Message, *args, **kwargs):
            if not flag:
                logging.debug("Команда /%s временно отключена.", name)
                return
            # aiogram v3 может передавать служебные параметры в kwargs,
            # такие как ``dispatcher`` или другие технические ключи.
            # Чтобы предотвратить ошибки "unexpected keyword argument",
            # сначала удаляем ``dispatcher``, затем фильтруем оставшиеся
            # параметры на основе сигнатуры пользовательской функции.
            if kwargs:
                kwargs.pop("dispatcher", None)
                sig = inspect.signature(func)
                if not any(
                    p.kind == inspect.Parameter.VAR_KEYWORD
                    for p in sig.parameters.values()
                ):
                    kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}
            return await func(message, *args, **kwargs)

        if router:
            router.message.register(wrapper, Command(commands=[name]))
        COMMAND_REGISTRY.append(
            {
                "name": name,
                "handler": wrapper,
                "router": router,
            }
        )
        return wrapper

    return decorator
