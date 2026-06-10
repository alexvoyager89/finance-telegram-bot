"""Проверка и разбор сумм из сообщений пользователя."""


def parse_amount_input(text: str) -> tuple[float | None, str | None]:
    """
    Проверяет ввод суммы: только число, больше нуля.
    Возвращает (сумма, None) или (None, код_ошибки).
    """
    t = text.strip().replace(" ", "")
    if not t:
        return None, "empty"

    normalized = t.replace(",", ".")
    if normalized.count(".") > 1:
        return None, "not_a_number"

    for char in normalized:
        if char != "." and not char.isdigit():
            return None, "not_a_number"

    try:
        value = float(normalized)
    except ValueError:
        return None, "not_a_number"

    if value <= 0:
        return None, "not_positive"

    return value, None


def parse_amount(args: list[str]) -> tuple[float | None, str | None]:
    """Парсит сумму из аргументов команды /income или /expense."""
    if len(args) != 1:
        return None, "missing"
    amount, err = parse_amount_input(args[0])
    if err == "empty":
        return None, "missing"
    return amount, err
