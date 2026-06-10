"""Тексты ответов бота (форматирование с эмодзи и HTML)."""

import math
from html import escape as html_escape

LINE = "─" * 24

ERR_ONLY_NUMBER = (
    f"⚠️ <b>Неверный ввод</b>\n{LINE}\n"
    "Введи только число.\n"
    "Пример: <code>1000</code> или <code>99,50</code>"
)
ERR_AMOUNT_POSITIVE = (
    f"⚠️ <b>Неверная сумма</b>\n{LINE}\n"
    "Сумма должна быть больше нуля."
)


def _group_thousands_int(n: int) -> str:
    n = int(n)
    neg = n < 0
    s = str(abs(n))
    parts: list[str] = []
    while s:
        parts.append(s[-3:])
        s = s[:-3]
    body = " ".join(reversed(parts))
    return ("-" if neg else "") + body


def format_money(value: float) -> str:
    v = float(value)
    if not math.isfinite(v):
        return str(v)
    av = abs(v)
    near_int = abs(av - round(av)) <= max(1e-9, 1e-9 * av)
    if near_int:
        return _group_thousands_int(int(round(v)))
    sign = "-" if v < 0 else ""
    text = f"{av:.2f}".rstrip("0").rstrip(".")
    if "." not in text:
        return sign + _group_thousands_int(int(text))
    left, right = text.split(".", 1)
    return sign + _group_thousands_int(int(left)) + "." + right


def format_amount_error(err: str) -> str:
    if err == "not_a_number":
        return ERR_ONLY_NUMBER
    if err == "not_positive":
        return ERR_AMOUNT_POSITIVE
    return ERR_ONLY_NUMBER


def _sorted_categories(by_cat: dict) -> list[tuple[str, dict]]:
    return sorted(
        by_cat.items(),
        key=lambda item: float(item[1].get("sum", 0)),
        reverse=True,
    )


def _category_lines(
    by_cat: dict,
    sign: str,
    limit: int | None = 5,
    header: str = "   <i>По категориям:</i>",
) -> list[str]:
    if not by_cat:
        return []
    items = _sorted_categories(by_cat)
    if limit is not None:
        items = items[:limit]
    lines = [header] if header else []
    for cat, data in items:
        total = float(data.get("sum", 0))
        count = int(data.get("count", 0))
        lines.append(
            f"   • {html_escape(cat)}: <b>{sign}{format_money(total)}</b> "
            f"({count} оп.)"
        )
    return lines


def _top_expense_category(expense_by: dict) -> str | None:
    if not expense_by:
        return None
    cat, data = _sorted_categories(expense_by)[0]
    total = float(data.get("sum", 0))
    count = int(data.get("count", 0))
    if total <= 0:
        return None
    return (
        "🏆 <b>Самая большая категория расходов</b>\n"
        f"   {html_escape(cat)}: <b>−{format_money(total)}</b> "
        f"({count} операций)"
    )


def fmt_start_message() -> str:
    return (
        "👋 <b>Финансовый помощник</b>\n"
        f"{LINE}\n\n"
        "🧠 <b>Как пользоваться</b>\n"
        "• Нажми <b>/</b> — список команд\n"
        "• Или кнопки внизу: Доход, Расход, Баланс, Статистика\n"
        "• Кнопка <code>/start</code> — вернуть это меню\n\n"
        "🧾 <b>Команды</b>\n"
        "• <code>/income 1000 зарплата</code>\n"
        "• <code>/expense 200 еда</code>\n"
        "• <code>/balance</code> — баланс\n"
        "• <code>/stats</code> — сводка\n"
        "• <code>/undo</code> — отменить последнюю операцию\n\n"
        "↩️ Или кнопка <b>Отменить последнюю</b> внизу."
    )


def fmt_balance_message(balance: float) -> str:
    return (
        "💰 <b>Баланс</b>\n"
        f"{LINE}\n"
        f"📌 <b>{format_money(balance)}</b>"
    )


def fmt_transaction_message(
    kind: str, amount: float, category: str, balance: float
) -> str:
    if kind == "income":
        icon, title, sign = "✅", "Доход", "+"
    else:
        icon, title, sign = "❌", "Расход", "−"
    return (
        f"{icon} <b>{title}</b>\n"
        f"{LINE}\n"
        f"🏷 Категория: <i>{html_escape(category)}</i>\n"
        f"💵 Сумма: <b>{sign}{format_money(amount)}</b>\n"
        f"{LINE}\n"
        f"📌 Баланс: <b>{format_money(balance)}</b>"
    )


def fmt_stats_message(stats: dict) -> str:
    income_by = stats.get("income_by_category") or {}
    expense_by = stats.get("expense_by_category") or {}
    income_count = int(stats.get("income_count", 0))
    expense_count = int(stats.get("expense_count", 0))
    total_ops = income_count + expense_count

    lines = [
        "📊 <b>Статистика</b>",
        LINE,
        "",
        "🔢 <b>Количество операций</b>",
        f"   Всего: <b>{total_ops}</b>",
        f"   ➕ доходов: <b>{income_count}</b>",
        f"   ➖ расходов: <b>{expense_count}</b>",
        "",
        "➕ <b>Доходы</b>",
        f"   Сумма: <b>+{format_money(stats['income_sum'])}</b>",
        *_category_lines(income_by, "+", limit=5),
        "",
        "➖ <b>Расходы</b>",
        f"   Операций: <b>{expense_count}</b>",
        f"   Общая сумма: <b>−{format_money(stats['expense_sum'])}</b>",
    ]

    top_expense = _top_expense_category(expense_by)
    if top_expense:
        lines.extend(["", top_expense])

    if expense_by:
        lines.extend(
            [
                "",
                "📂 <b>Расходы по категориям</b>",
                *_category_lines(expense_by, "−", limit=None, header=""),
            ]
        )
    elif expense_count == 0:
        lines.append("   <i>Расходов пока нет</i>")

    lines.extend(
        [
            "",
            LINE,
            f"📌 <b>Итоговый баланс:</b> {format_money(stats['balance'])}",
        ]
    )
    return "\n".join(lines)


def fmt_choose_category(kind: str) -> str:
    if kind == "income":
        return f"➕ <b>Доход</b>\n{LINE}\nВыбери категорию:"
    return f"➖ <b>Расход</b>\n{LINE}\nВыбери категорию:"


def fmt_enter_amount(kind: str) -> str:
    example = "1500" if kind == "income" else "300"
    return (
        "✍️ <b>Введи сумму</b>\n"
        f"{LINE}\n"
        f"Только число, например: <code>{example}</code>"
    )


def fmt_hint(text: str) -> str:
    return f"📝 {text}"


def fmt_warning(text: str) -> str:
    return f"⚠️ {text}"


def fmt_undo_success(operation: dict, balance: float) -> str:
    kind = operation["kind"]
    amount = float(operation["amount"])
    category = str(operation["category"])
    if kind == "income":
        label, sign = "доход", "+"
    else:
        label, sign = "расход", "−"
    return (
        "↩️ <b>Операция отменена</b>\n"
        f"{LINE}\n"
        f"Убран {label}:\n"
        f"🏷 <i>{html_escape(category)}</i>\n"
        f"💵 <b>{sign}{format_money(amount)}</b>\n"
        f"{LINE}\n"
        f"📌 Баланс: <b>{format_money(balance)}</b>"
    )


def fmt_undo_empty() -> str:
    return (
        "↩️ <b>Отмена</b>\n"
        f"{LINE}\n"
        "Нет операций для отмены.\n"
        "Сначала добавь доход или расход."
    )
