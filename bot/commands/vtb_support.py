from aiogram import Router, types

from bot.config.flags import VTB_SUPPORT_ENABLE
from bot.utils.command_registry import command

router = Router()


@command("vtb_support", flag=VTB_SUPPORT_ENABLE, router=router)
async def handle_vtb_support(message: types.Message) -> None:
    text = "Телефон поддержки ВТБ - +74959818081"
    await message.answer(text)
