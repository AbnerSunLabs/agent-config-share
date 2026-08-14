from typing import Any

_REDACTED = "***"


def looks_like_secret(text: str) -> bool:
    if not text:
        return False
    if text.startswith("sk-"):
        return True
    # 长 token 且无空白，疑似密钥
    if len(text) >= 32 and text.strip() == text and " " not in text:
        return True
    return False


def _redact_value(value: Any) -> Any:
    if isinstance(value, str) and looks_like_secret(value):
        return _REDACTED
    return value


def safe_print(*args: Any, **kwargs: Any) -> None:
    """打印时脱敏疑似密钥，避免日志泄露。"""
    redacted = tuple(_redact_value(arg) for arg in args)
    print(*redacted, **kwargs)
