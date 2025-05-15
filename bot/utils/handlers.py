from bot.commands.start import register_start_handler
from bot.commands.help import register_help_handler
from bot.commands.docs import register_docs_handler
from bot.commands.announce import register_announce_handler
from bot.commands.add_chat import register_add_chat_handler
from bot.commands.remove_chat import register_remove_chat_handler
from bot.commands.get_access import register_get_access_handler
from bot.commands.search import register_search_handler
from bot.commands.best_qa import register_best_qa_handler
from bot.commands.best_qa_stat import register_best_qa_stat_handler
from bot.commands.chat_list import register_chat_list_handler
from bot.commands.epa_guide import register_epa_guide_handler
from bot.commands.epa_contacts import register_epa_contacts_handler
from bot.commands.vtb_support import register_vtb_support_handler
from bot.modules.buttons import register_button_handlers
from bot.messages.messages import register_message_handlers


def register_handlers(dp):
    """
    Регистрирует все обработчики бота.
    """
    register_start_handler(dp)
    register_help_handler(dp)
    register_docs_handler(dp)
    register_search_handler(dp)
    register_announce_handler(dp)
    register_add_chat_handler(dp)
    register_remove_chat_handler(dp)
    register_get_access_handler(dp)
    register_best_qa_handler(dp)
    register_best_qa_stat_handler(dp)
    register_chat_list_handler(dp)
    register_epa_guide_handler(dp)
    register_epa_contacts_handler(dp)
    register_vtb_support_handler(dp)
    register_button_handlers(dp)
    register_message_handlers(dp)
