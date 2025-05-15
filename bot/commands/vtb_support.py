from aiogram import Router, types
from aiogram.filters import Command
from bot.config.flags import VTB_SUPPORT_ENABLE

router = Router()

@router.message(Command("vtb_support", prefix="/"))
async def handle_vtb_support(message: types.Message) -> None:
    if not VTB_SUPPORT_ENABLE:
        await message.answer("Команда временно отключена.")
        return None

    text = (
        "Телефон поддержки ВТБ - +74959818081"
    )
    await message.answer(text)

def register_vtb_support_handler(dp) -> None:
    dp.message.register(handle_vtb_support, Command(commands=["vtb_support"]))
