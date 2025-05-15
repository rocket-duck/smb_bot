from aiogram import Router, types
from aiogram.filters import Command
from bot.config.flags import GET_EPA_GUIDE_ENABLE

router = Router()

@router.message(Command("epa_guide", prefix="/"))
async def handle_epa_guide(message: types.Message) -> None:
    if not GET_EPA_GUIDE_ENABLE:
        await message.answer("Команда временно отключена.")
        return None

    text = (
        "Авторизация по старой цепочке (ЕПА-3): https://sfera.inno.local/knowledge/pages?id=1513112\n"
        "Авторизация по новой цепочке (ЕПА-10): https://sfera.inno.local/knowledge/pages?id=1513113"
    )
    await message.answer(text)

def register_epa_guide_handler(dp) -> None:
    dp.message.register(handle_epa_guide, Command(commands=["epa_guide"]))
