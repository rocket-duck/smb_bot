import re

_AUTH_ISSUE_PATTERNS = [
    r"епа.*проблем",
    r"не получается.*вход",
    r"при авторизац",
    r"ошибка при попытке авторизац",
    r"не можем авторизов",
    r"ошибка входа",
    r"не могу (?:войти|зайти)",
    r"проблема с входом",
    r"проблемы с авторизац",
    r"на контуре.*входа",
    r"не удается.*(?:войти|авторизоваться)",
    r"у епа нет.*проблем",
    r"не удаётся осуществить вход",
    r"при авторизации такая ошибка",
    r"такая ошибка при попытке авторизации",
    r"не можем авторизоваться",
    r"проблемы при логине",
    r"логин не удаётся",
    r"не открывается.*авторизац",
    r"не могу залогиниться",
    r"войти не получается",
]
_AUTH_ISSUE_REGEX = re.compile(r"(?:{})".format("|".join(_AUTH_ISSUE_PATTERNS)), flags=re.IGNORECASE)


def get_auth_issue_response(text: str, enabled: bool) -> str | None:
    """
    If enabled and the message text matches known authorization issue patterns,
    returns the prompt message to ask for auth logs. Otherwise returns None.
    """
    if not enabled:
        return None
    if _AUTH_ISSUE_REGEX.search(text or ""):
        return ("Что бы могли вам помочь, пожалуйста, приложите логи авторизации в которых видно полученную ошибку "
                "при авторизации и респонс. Так же можете указать код ошибки, который отображается на экране "
                "устройства.")
    return None
