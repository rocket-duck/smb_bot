from aiogram import Router, types
from aiogram.filters import Command
from bot.config.flags import GET_EPA_CONTACTS_ENABLE

router = Router()

@router.message(Command("epa_contacts", prefix="/"))
async def handle_epa_contacts(message: types.Message) -> None:
    if not GET_EPA_CONTACTS_ENABLE:
        await message.answer("Команда временно отключена.")
        return None

    text = (
        "Контакты ЕПА для связи: https://sfera.inno.local/knowledge/pages?id=1524162"
    )
    await message.answer(text)

def register_epa_contacts_handler(dp) -> None:
    dp.message.register(handle_epa_contacts, Command(commands=["epa_contacts"]))
