from bot.services.menu_service import create_menu
from bot.config.flags import DOCS_ENABLE
import logging

logger = logging.getLogger(__name__)

class DocsServiceError(Exception):
    """Базовый класс ошибок сервиса документации."""

class DocsServiceDisabled(DocsServiceError):
    """Сервис документов временно отключен."""

class EmptyDocsMenu(DocsServiceError):
    """Меню документов пусто."""

def get_docs_menu(user_id: int):
    """
    Возвращает меню документов и текст для главного меню.
    :raises DocsServiceDisabled: если DOCS_ENABLE=False.
    :raises EmptyDocsMenu: если меню пустое.
    """
    if not DOCS_ENABLE:
        logger.warning("DocsService: сервис документов отключен.")
        raise DocsServiceDisabled("Документы временно недоступны.")

    menu, _ = create_menu(user_id=user_id)
    if not menu.inline_keyboard:
        logger.warning("DocsService: меню документов пустое.")
        raise EmptyDocsMenu("Нет доступных документов.")

    main_menu_text = "Вот какие ссылки я знаю.\nВыберите из меню ниже:"
    return menu, main_menu_text
