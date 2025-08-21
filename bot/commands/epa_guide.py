from aiogram import Router, types

from bot.config.flags import GET_EPA_GUIDE_ENABLE
from bot.utils.command_registry import command

router = Router()


@command("epa_guide", flag=GET_EPA_GUIDE_ENABLE, router=router)
async def handle_epa_guide(message: types.Message) -> None:
    text = (
        "Авторизация по старой цепочке (ЕПА-3): https://sfera.inno.local/knowledge/pages?id=1513112\n"
        "Авторизация по новой цепочке (ЕПА-10): https://sfera.inno.local/knowledge/pages?id=1513113"
    )
    await message.answer(text)
