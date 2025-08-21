from aiogram import Router, types

from bot.config.flags import GET_EPA_CONTACTS_ENABLE
from bot.utils.command_registry import command

router = Router()


@command("epa_contacts", flag=GET_EPA_CONTACTS_ENABLE, router=router)
async def handle_epa_contacts(message: types.Message) -> None:
    text = (
        "Контакты ЕПА для связи: https://sfera.inno.local/knowledge/pages?id=1524162"
    )
    await message.answer(text)
