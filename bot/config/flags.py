# Ответ на ключевые слова
KEYWORD_RESPONSES_ENABLE = True
TIMEOUT_RESPONSES_ENABLE = True
WHO_REQUEST_ENABLE = True
BOT_TAG_ENABLE = True
MASLINA_ENABLE = True

# Commands
ADD_CHAT_ENABLE = True
REMOVE_CHAT_ENABLE = True
ANNOUNCE_ENABLE = True
DOCS_ENABLE = True
HELP_ENABLE = True
SEARCH_ENABLE = True
BEST_QA_ENABLE = True
BEST_QA_STAT_ENABLE = True
GET_ACCESS_ENABLE = True
GET_CHAT_LIST = True
GET_EPA_GUIDE_ENABLE = True
GET_EPA_CONTACTS_ENABLE = True
VTB_SUPPORT_ENABLE = True

# Fan triggers
TIMEOUT_MINUTES: int = 20
FAN_TRIGGER_PROBABILITY: float = 0.25
TRIGGER_PATTERNS = [
    r"\bа кто\b",
    r"\bа почему\b",
    r"\bа когда\b",
    r"\bа где\b",
    r"\bа как\b"
]
