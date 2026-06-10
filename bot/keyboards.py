"""Клавиатуры Telegram (кнопки внизу чата)."""

from telegram import KeyboardButton, ReplyKeyboardMarkup

from bot.config import (
    BTN_BACK,
    BTN_BALANCE,
    BTN_EXPENSE,
    BTN_INCOME,
    BTN_START,
    BTN_STATS,
    BTN_UNDO,
    DEFAULT_CATEGORY,
    EXPENSE_CATEGORIES,
    INCOME_CATEGORIES,
)


def main_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню."""
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton(BTN_START)],
            [KeyboardButton(BTN_BALANCE), KeyboardButton(BTN_STATS)],
            [KeyboardButton(BTN_INCOME), KeyboardButton(BTN_EXPENSE)],
            [KeyboardButton(BTN_UNDO)],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def category_keyboard(kind: str) -> ReplyKeyboardMarkup:
    """Клавиатура выбора категории для дохода или расхода."""
    categories = INCOME_CATEGORIES if kind == "income" else EXPENSE_CATEGORIES
    rows: list[list[KeyboardButton]] = [[KeyboardButton(BTN_BACK)]]

    for i in range(0, len(categories), 2):
        row = [KeyboardButton(categories[i])]
        if i + 1 < len(categories):
            row.append(KeyboardButton(categories[i + 1]))
        rows.append(row)

    rows.append([KeyboardButton(DEFAULT_CATEGORY)])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, is_persistent=True)
