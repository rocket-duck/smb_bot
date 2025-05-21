import logging
import functools
from dataclasses import dataclass
from typing import List
from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeAllGroupChats
from bot.config import flags

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CommandDef:
    command: str
    description: str
    flag: bool
    private_chat: bool
    group_chat: bool
    visible_in_help: bool
    is_admin: bool


# Declarative list of all commands
COMMAND_DEFINITIONS: List[CommandDef] = [
    CommandDef("help", "Получить справку", flags.HELP_ENABLE, True, True, False, False),
    CommandDef("docs", "Открыть документацию", flags.DOCS_ENABLE, True, True, True, False),
    CommandDef("announce", "Сделать объявление", flags.ANNOUNCE_ENABLE, True, False, True, True),
    CommandDef("search", "Спросить chatGPT о тестировании", flags.SEARCH_ENABLE, True, True, True, False),
    CommandDef("add_chat", "Добавить чат в список рассылки анонсов", flags.ADD_CHAT_ENABLE, False, False, False, False),
    CommandDef("remove_chat", "Удалить чат из списка рассылки анонсов", flags.REMOVE_CHAT_ENABLE, False, False, False, False),
    CommandDef("best_qa", "Выбрать лучшего тестировщика дня", flags.BEST_QA_ENABLE, False, True, True, False),
    CommandDef("best_qa_stat", "Получить список победителей тестировщика дня", flags.BEST_QA_STAT_ENABLE, False, True, True, False),
    # CommandDef("get_access", "Запросить доступ", flags.GET_ACCESS_ENABLE, True, False, True, False),
    # CommandDef("chat_list", "Список добавленных чатов", flags.GET_CHAT_LIST, True, False, True, True),
    CommandDef("epa_guide", "Информация по авторизации в ЕПА и кейсу Ж", flags.GET_EPA_GUIDE_ENABLE, True, True, True, False),
    CommandDef("epa_contacts", "Контактные данные ЕПА для связи", flags.GET_EPA_CONTACTS_ENABLE, True, True, True, False),
    CommandDef("vtb_support", "Телефон службы поддержки ВТБ", flags.VTB_SUPPORT_ENABLE, True, True, True, False),
]


@functools.lru_cache(maxsize=None)
def get_all_command_defs(user_is_admin: bool = False) -> List[CommandDef]:
    """
    Returns all CommandDef entries which are enabled by flag and (if is_admin) user permissions.
    """
    defs = [
        cmd for cmd in COMMAND_DEFINITIONS
        if cmd.flag and (not cmd.is_admin or user_is_admin)
    ]
    logger.debug(f"Filtered commands (admin={user_is_admin}): {[c.command for c in defs]}")
    return defs


def build_bot_commands_for_scope(cmd_defs: List[CommandDef], scope_attr: str) -> List[BotCommand]:
    """
    Build BotCommand list for given scope attribute ('private_chat' or 'group_chat').
    """
    cmds = [
        BotCommand(command=cmd.command, description=cmd.description)
        for cmd in cmd_defs
        if getattr(cmd, scope_attr) and cmd.visible_in_help
    ]
    logger.info(f"Prepared {len(cmds)} commands for scope {scope_attr}")
    return cmds


async def set_bot_commands(tg_bot: Bot, user_is_admin: bool = False) -> None:
    """
    Set bot commands for private and group scopes based on definitions.
    """
    cmd_defs = get_all_command_defs(user_is_admin)
    # Private chats
    private_cmds = build_bot_commands_for_scope(cmd_defs, "private_chat")
    await tg_bot.set_my_commands(private_cmds, scope=BotCommandScopeDefault())
    # Group chats
    group_cmds = build_bot_commands_for_scope(cmd_defs, "group_chat")
    await tg_bot.set_my_commands(group_cmds, scope=BotCommandScopeAllGroupChats())
