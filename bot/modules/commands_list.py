from typing import Any

from aiogram import Bot
from aiogram.types import BotCommand

from bot.config import flags

# Декларативное описание команд
COMMAND_DEFINITIONS: list[dict[str, Any]] = [
    {
        "command": "help",
        "description": "Получить справку",
        "flag": flags.HELP_ENABLE,
        "private_chat": True,
        "group_chat": True,
        "visible_in_help": False,
    },
    {
        "command": "docs",
        "description": "Открыть документацию",
        "flag": flags.DOCS_ENABLE,
        "private_chat": True,
        "group_chat": True,
        "visible_in_help": True,
    },
    {
        "command": "announce",
        "description": "Сделать объявление",
        "flag": flags.ANNOUNCE_ENABLE,
        "private_chat": True,
        "group_chat": False,
        "visible_in_help": True,
    },
    {
        "command": "search",
        "description": "Спросить chatGPT о тестировании",
        "flag": flags.SEARCH_ENABLE,
        "private_chat": True,
        "group_chat": True,
        "visible_in_help": True,
    },
    {
        "command": "add_chat",
        "description": "Добавить чат в список рассылки анонсов",
        "flag": flags.ADD_CHAT_ENABLE,
        "private_chat": False,
        "group_chat": False,
        "visible_in_help": False,
    },
    {
        "command": "remove_chat",
        "description": "Удалить чат из списка рассылки анонсов",
        "flag": flags.REMOVE_CHAT_ENABLE,
        "private_chat": False,
        "group_chat": False,
        "visible_in_help": False,
    },
    {
        "command": "best_qa",
        "description": "Выбрать лучшего тестировщика дня",
        "flag": flags.BEST_QA_ENABLE,
        "private_chat": False,
        "group_chat": True,
        "visible_in_help": True,
    },
    {
        "command": "best_qa_stat",
        "description": "Получить список победителей тестировщика дня",
        "flag": flags.BEST_QA_STAT_ENABLE,
        "private_chat": False,
        "group_chat": True,
        "visible_in_help": True,
    },
    {
        "command": "chat_list",
        "description": "Список добавленных чатов",
        "flag": flags.GET_CHAT_LIST,
        "private_chat": True,
        "group_chat": False,
        "visible_in_help": True,
    },
    {
        "command": "epa_guide",
        "description": "Информация по авторизации в ЕПА и кейсу Ж",
        "flag": flags.GET_EPA_GUIDE_ENABLE,
        "private_chat": True,
        "group_chat": True,
        "visible_in_help": True,
    },
    {
        "command": "epa_contacts",
        "description": "Контактные данные ЕПА для связи",
        "flag": flags.GET_EPA_CONTACTS_ENABLE,
        "private_chat": True,
        "group_chat": True,
        "visible_in_help": True,
    },
    {
        "command": "vtb_support",
        "description": "Телефон службы поддержки ВТБ",
        "flag": flags.VTB_SUPPORT_ENABLE,
        "private_chat": True,
        "group_chat": True,
        "visible_in_help": True,
    },
    {
        "command": "dushnila_weekly",
        "description": "Топ душнил недели",
        "flag": flags.DUSHNILA_WEEKLY_ENABLE,
        "private_chat": False,
        "group_chat": True,
        "visible_in_help": True,
    },
    {
        "command": "dushnila_me",
        "description": "Личная статистика душности",
        "flag": flags.DUSHNILA_ME_ENABLE,
        "private_chat": False,
        "group_chat": True,
        "visible_in_help": True,
    },
    {
        "command": "dushnila_why",
        "description": "За что начислены баллы душности участнику",
        "flag": flags.DUSHNILA_WHY_ENABLE,
        "private_chat": False,
        "group_chat": True,
        "visible_in_help": True,
    },
    {
        "command": "dushnila_reset_week",
        "description": "Сбросить недельный рейтинг душнил",
        "flag": flags.DUSHNILA_RESET_WEEK_ENABLE,
        "private_chat": False,
        "group_chat": True,
        "visible_in_help": False,
    },
]


def add_command(
    commands: list[dict[str, Any]],
    command_name: str,
    description: str,
    flag: bool,
    private_chat: bool = True,
    group_chat: bool = True,
    visible_in_help: bool = True,
) -> None:
    if flag:
        commands.append(
            {
                "command": BotCommand(command=command_name, description=description),
                "private_chat": private_chat,
                "group_chat": group_chat,
                "visible_in_help": visible_in_help,
            }
        )


def get_all_commands() -> list[dict[str, Any]]:
    commands: list[dict[str, Any]] = []
    for cmd_def in COMMAND_DEFINITIONS:
        add_command(
            commands,
            command_name=cmd_def["command"],
            description=cmd_def["description"],
            flag=cmd_def["flag"],
            private_chat=cmd_def["private_chat"],
            group_chat=cmd_def["group_chat"],
            visible_in_help=cmd_def["visible_in_help"],
        )
    return commands


def get_commands_for_scope(
    commands: list[dict[str, Any]], scope: str
) -> list[BotCommand]:
    return [
        cmd["command"]
        for cmd in commands
        if cmd.get(scope) and cmd.get("visible_in_help")
    ]


async def set_bot_commands(bot: Bot) -> None:
    commands = get_all_commands()
    from aiogram.types import BotCommandScopeAllGroupChats, BotCommandScopeDefault

    private_commands = get_commands_for_scope(commands, "private_chat")
    await bot.set_my_commands(private_commands, scope=BotCommandScopeDefault())
    group_commands = get_commands_for_scope(commands, "group_chat")
    await bot.set_my_commands(group_commands, scope=BotCommandScopeAllGroupChats())
