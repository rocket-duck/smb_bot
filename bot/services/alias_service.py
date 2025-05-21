import re
from typing import List, Dict, Any


def extend_aliases(links: List[Dict[str, Any]]) -> None:
    """
    Auto-extend aliases for each entry in the LINKS list:
    - include the full lowercase name
    - include the name without punctuation
    """
    for entry in links:
        entry.setdefault("aliases", [])
        name_lower = entry["name"].lower()
        # full lowercase name
        entry["aliases"].append(name_lower)
        # name without punctuation
        entry["aliases"].append(re.sub(r"[^\w\s]", "", name_lower))
        # remove duplicates, preserving order
        entry["aliases"] = list(dict.fromkeys(entry["aliases"]))
