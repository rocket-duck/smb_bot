from html import escape
from typing import List, Tuple

def format_response(results: List[Tuple[str, str]]) -> str:
    """
    Formats a list of (name, url) pairs into a human-readable string,
    with each entry on a new line: "name: url". Escapes HTML in name and URL.

    :param results: list of tuples (link name, link URL)
    :return: formatted multi-line string
    """
    lines: List[str] = []
    for name, url in results:
        safe_name = escape(name)
        safe_url = escape(url)
        lines.append(f"{safe_name}: {safe_url}")
    return "\n".join(lines)