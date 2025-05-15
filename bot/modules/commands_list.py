from typing import List, Dict, Any
from aiogram import Bot
from aiogram.types import BotCommand
from bot.config import flags


# Декларативное описание команд
COMMAND_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "command": "help",
        "description": "Получить справку",
        "flag": flags.HELP_ENABLE,
        "private_chat": True,
        "group_chat": True,
        "visible_in_help": False,
        "is_admin": False,
    },
    {
        "command": "docs",
        "description": "Открыть документацию",
        "flag": flags.DOCS_ENABLE,
        "private_chat": True,
        "group_chat": True,
        "visible_in_help": True,
        "is_admin": False,
    },
    {
        "command": "announce",
        "description": "Сделать объявление",
        "flag": flags.ANNOUNCE_ENABLE,
        "private_chat": True,
        "group_chat": False,
        "visible_in_help": True,
        "is_admin": True,  # Только для администраторов
    },
    {
        "command": "search",
        "description": "Спросить chatGPT о тестировании",
        "flag": flags.SEARCH_ENABLE,
        "private_chat": True,
        "group_chat": True,
        "visible_in_help": True,
        "is_admin": False,
    },
    {
        "command": "add_chat",
        "description": "Добавить чат в список рассылки анонсов",
        "flag": flags.ADD_CHAT_ENABLE,
        "private_chat": False,
        "group_chat": False,
        "visible_in_help": False,
        "is_admin": False,
    },
    {
        "command": "remove_chat",
        "description": "Удалить чат из списка рассылки анонсов",
        "flag": flags.REMOVE_CHAT_ENABLE,
        "private_chat": False,
        "group_chat": False,
        "visible_in_help": False,
        "is_admin": False,
    },
    {
        "command": "best_qa",
        "description": "Выбрать лучшего тестировщика дня",
        "flag": flags.BEST_QA_ENABLE,
        "private_chat": False,
        "group_chat": True,
        "visible_in_help": True,
        "is_admin": False,
    },
    {
        "command": "best_qa_stat",
        "description": "Получить список победителей тестировщика дня",
        "flag": flags.BEST_QA_STAT_ENABLE,
        "private_chat": False,
        "group_chat": True,
        "visible_in_help": True,
        "is_admin": False,
    },
    {
        "command": "get_access",
        "description": "Запросить доступ",
        "flag": flags.GET_ACCESS_ENABLE,
        "private_chat": True,
        "group_chat": False,
        "visible_in_help": True,
        "is_admin": False,
    },
    # Новая команда для администраторов:
    {
        "command": "chat_list",
        "description": "Список добавленных чатов",
        "flag": flags.GET_CHAT_LIST,
        "private_chat": True,
        "group_chat": False,
        "visible_in_help": True,
        "is_admin": True,
    },
    {
        "command": "epa_guide",
        "description": "Информация по авторизации в ЕПА и кейсу Ж",
        "flag": flags.GET_EPA_GUIDE_ENABLE,
        "private_chat": True,
        "group_chat": True,
        "visible_in_help": True,
        "is_admin": False,
    },
    {
        "command": "epa_contacts",
        "description": "Контактные данные ЕПА для связи",
        "flag": flags.GET_EPA_CONTACTS_ENABLE,
        "private_chat": True,
        "group_chat": True,
        "visible_in_help": True,
        "is_admin": False,
    },
    {
        "command": "vtb_support",
        "description": "Телефон службы поддержки ВТБ",
        "flag": flags.VTB_SUPPORT_ENABLE,
        "private_chat": True,
        "group_chat": True,
        "visible_in_help": True,
        "is_admin": False,
    },
]


def add_command(commands: List[Dict[str, Any]],
                command_name: str,
                description: str,
                flag: bool,
                private_chat: bool = True,
                group_chat: bool = True,
                visible_in_help: bool = True,
                is_admin: bool = False) -> None:
    if flag:
        commands.append({
            "command": BotCommand(command=command_name,
                                  description=description),
            "private_chat": private_chat,
            "group_chat": group_chat,
            "visible_in_help": visible_in_help,
            "is_admin": is_admin,
        })


def get_all_commands(user_is_admin: bool = False) -> List[Dict[str, Any]]:
    commands: List[Dict[str, Any]] = []
    for cmd_def in COMMAND_DEFINITIONS:
        if cmd_def.get("is_admin", False) and not user_is_admin:
            continue
        add_command(commands,
                    command_name=cmd_def["command"],
                    description=cmd_def["description"],
                    flag=cmd_def["flag"],
                    private_chat=cmd_def["private_chat"],
                    group_chat=cmd_def["group_chat"],
                    visible_in_help=cmd_def["visible_in_help"],
                    is_admin=cmd_def.get("is_admin", False))
    return commands


def get_commands_for_scope(commands: List[Dict[str, Any]],
                           scope: str) -> List[BotCommand]:
    return [cmd["command"] for cmd in commands if cmd.get(scope)
            and cmd.get("visible_in_help")]


async def set_bot_commands(bot: Bot, user_is_admin: bool = False) -> None:
    commands = get_all_commands(user_is_admin=user_is_admin)
    from aiogram.types import (BotCommandScopeDefault,
                               BotCommandScopeAllGroupChats)
    private_commands = get_commands_for_scope(commands,
                                              "private_chat")
    await bot.set_my_commands(private_commands,
                              scope=BotCommandScopeDefault())
    group_commands = get_commands_for_scope(commands, "group_chat")
    await bot.set_my_commands(group_commands,
                              scope=BotCommandScopeAllGroupChats())
