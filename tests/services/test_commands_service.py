import pytest
import bot.services.commands_service as service
from aiogram.types import BotCommand
from bot.services.commands_service import CommandDef, get_all_command_defs, build_bot_commands_for_scope, set_bot_commands
from types import SimpleNamespace

def make_command_def(
    cmd: str,
    desc: str,
    flag: bool,
    private: bool,
    group: bool,
    visible: bool,
    admin: bool
):
    return CommandDef(
        command=cmd,
        description=desc,
        flag=flag,
        private_chat=private,
        group_chat=group,
        visible_in_help=visible,
        is_admin=admin
    )

def test_get_all_command_defs_filters_flags_and_admin(monkeypatch):
    # Prepare a mix of CommandDef entries
    defs = [
        make_command_def("a", "A", True, True, True, True, False),
        make_command_def("b", "B", False, True, True, True, False),
        make_command_def("c", "C", True, True, True, True, True),
    ]
    monkeypatch.setattr(service, "COMMAND_DEFINITIONS", defs)
    # As non-admin: should exclude b (flag False) and c (is_admin True)
    out1 = get_all_command_defs(user_is_admin=False)
    assert [d.command for d in out1] == ["a"]
    # As admin: should include a and c
    out2 = get_all_command_defs(user_is_admin=True)
    assert sorted(d.command for d in out2) == ["a", "c"]

def test_build_bot_commands_for_scope_filters_and_formats(monkeypatch):
    # Stub BotCommand to simple object
    monkeypatch.setattr(service, "BotCommand", lambda *args, **kwargs: SimpleNamespace(command=kwargs.get("command"), description=kwargs.get("description")))
    # Create two defs, one for private only, one for group only, one invisible
    defs = [
        make_command_def("p", "Priv desc", True, True, False, True, False),
        make_command_def("g", "Group desc", True, False, True, True, False),
        make_command_def("v", "Vis desc", True, True, True, False, False),
    ]
    # Private scope
    private_cmds = build_bot_commands_for_scope(defs, "private_chat")
    assert isinstance(private_cmds, list)
    assert [cmd.command for cmd in private_cmds] == ["p"]
    # Group scope
    group_cmds = build_bot_commands_for_scope(defs, "group_chat")
    assert [cmd.command for cmd in group_cmds] == ["g"]

@pytest.mark.asyncio
async def test_set_bot_commands_invokes_api_with_correct_scopes(monkeypatch):
    # Stub build_bot_commands_for_scope to return predictable lists
    monkeypatch.setattr(
        service,
        "build_bot_commands_for_scope",
        lambda defs, scope_attr: [SimpleNamespace(command="x")] if scope_attr == "private_chat" else [SimpleNamespace(command="y")]
    )
    # Dummy bot that captures calls
    calls = []
    class DummyBot:
        async def set_my_commands(self, commands, scope):
            calls.append((commands, scope))
    bot = DummyBot()
    # Run set_bot_commands
    await set_bot_commands(bot, user_is_admin=False)
    # Expect two calls: one for private, one for group
    assert len(calls) == 2
    private_cmds, private_scope = calls[0]
    group_cmds, group_scope = calls[1]
    assert [c.command for c in private_cmds] == ["x"]
    from aiogram.types import BotCommandScopeDefault, BotCommandScopeAllGroupChats
    assert isinstance(private_scope, BotCommandScopeDefault)
    assert [c.command for c in group_cmds] == ["y"]
    assert isinstance(group_scope, BotCommandScopeAllGroupChats)
