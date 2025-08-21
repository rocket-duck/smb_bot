import re

from bot.dicts.errors_dict import raw_errors


def _build_code_pattern(code: str) -> str:
    """
    Build a regex pattern for the given error code,
    allowing both Latin 'B'/'b'/'В'/'в' and 'C'/'c'/'С'/'с'.
    """
    parts = []
    for ch in code:
        if ch in ("B", "В", "b", "в"):
            parts.append("[BbВв]")
        elif ch in ("C", "С", "c", "с"):
            parts.append("[CcСс]")
        elif ch in ("A", "А", "a", "а"):
            parts.append("[AaАа]")
        elif ch in ("V", "v"):
            parts.append("[Vv]")
        else:
            parts.append(re.escape(ch))
    return "".join(parts)


def build_error_defs(enabled: bool):
    """
    Generate error definitions based on raw_errors if enabled is True.
    """
    errors = []
    if enabled:
        for code, description in raw_errors:
            # Build full code pattern (letters B, C, A, V with variants)
            full_code_pattern = _build_code_pattern(code)
            alternatives = [full_code_pattern]
            lowered = code.lower()
            # Handle v2_ prefix: allow without v2_
            if lowered.startswith("v2_"):
                rest = code[3:]
                rest_pattern_full = _build_code_pattern(rest)
                alternatives.append(rest_pattern_full)
                # If rest has a leading letter, also allow digits-only
                if rest and rest[0] in ("B","В","b","в","C","С","c","с","A","А","a","а","V","v"):
                    digits = rest[1:]
                    alternatives.append(re.escape(digits))
            # Handle codes that start with a letter: allow without the letter
            elif code and code[0] in ("B","В","b","в","C","С","c","с","A","А","a","а","V","v"):
                rest = code[1:]
                rest_pattern_full = _build_code_pattern(rest)
                alternatives.append(rest_pattern_full)
                alternatives.append(re.escape(rest))
            # Combine alternatives into one pattern, with word boundaries
            code_pattern = "|".join(alternatives)
            regex = rf"\b(?:{code_pattern})\b"
            errors.append({
                "code": code,
                "description": description,
                "regex": regex
            })
    return errors
