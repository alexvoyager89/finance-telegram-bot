"""Обработка нажатий кнопок и ввода текста (не команд)."""

from telegram import Update
from telegram.ext import ContextTypes

from bot.config import (
    BTN_BACK,
    BTN_BALANCE,
    BTN_EXPENSE,
    BTN_INCOME,
    BTN_STATS,
    BTN_UNDO,
    DEFAULT_CATEGORY,
    EXPENSE_CATEGORIES,
    INCOME_CATEGORIES,
)
from bot.handlers.commands import start, stats_cmd, undo_cmd
from bot.handlers.common import clear_pending_state
from bot.handlers.decorators import log_handler
from bot.logger import log_action
from bot.keyboards import category_keyboard, main_keyboard
from bot.messages import (
    fmt_balance_message,
    fmt_choose_category,
    fmt_enter_amount,
    fmt_transaction_message,
    fmt_warning,
    format_amount_error,
)
from bot.parsers import parse_amount_input
from bot.storage import read_balance, record_expense_cat, record_income_cat


@log_handler("text")
async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is None:
        return

    user_id = update.effective_user.id
    text = (update.message.text or "").strip()
    pending = context.user_data.get("pending")
    pending_category = context.user_data.get("pending_category")
    pending_kind = context.user_data.get("pending_kind")

    if text == BTN_UNDO:
        log_action(update, "button_undo")
        clear_pending_state(context)
        await undo_cmd(update, context)
        return

    if text == BTN_BALANCE:
        log_action(update, "button_balance")
        clear_pending_state(context)
        balance = read_balance(user_id)
        await update.message.reply_text(
            fmt_balance_message(balance),
            parse_mode="HTML",
        )
        return

    if text == BTN_STATS:
        log_action(update, "button_stats")
        clear_pending_state(context)
        await stats_cmd(update, context)
        return

    if text == BTN_INCOME:
        log_action(update, "button_income")
        context.user_data["pending_kind"] = "income"
        context.user_data["pending_category"] = None
        context.user_data["pending"] = "choose_category"
        await update.message.reply_text(
            fmt_choose_category("income"),
            parse_mode="HTML",
            reply_markup=category_keyboard("income"),
        )
        return

    if text == BTN_EXPENSE:
        log_action(update, "button_expense")
        context.user_data["pending_kind"] = "expense"
        context.user_data["pending_category"] = None
        context.user_data["pending"] = "choose_category"
        await update.message.reply_text(
            fmt_choose_category("expense"),
            parse_mode="HTML",
            reply_markup=category_keyboard("expense"),
        )
        return

    if pending == "choose_category":
        if text == BTN_BACK:
            log_action(update, "button_back")
            await start(update, context)
            return

        kind = pending_kind if pending_kind in ("income", "expense") else "expense"
        allowed = INCOME_CATEGORIES if kind == "income" else EXPENSE_CATEGORIES
        allowed_lower = {c.lower() for c in allowed}
        if text != DEFAULT_CATEGORY and text.lower() not in allowed_lower:
            log_action(update, "category_invalid", f"text={text!r}")
            await update.message.reply_text(
                fmt_warning("Выбери категорию кнопкой из списка ниже."),
                parse_mode="HTML",
            )
            return

        log_action(update, "category_chosen", f"kind={kind} category={text}")
        context.user_data["pending_category"] = text
        context.user_data["pending"] = kind
        await update.message.reply_text(
            fmt_enter_amount(kind),
            reply_markup=main_keyboard(),
            parse_mode="HTML",
        )
        return

    if pending == "income":
        amount, err = parse_amount_input(text)
        if amount is None:
            log_action(update, "income_invalid", f"ошибка ввода: {err}")
            await update.message.reply_text(
                format_amount_error(err or "not_a_number"),
                parse_mode="HTML",
            )
            return
        category = pending_category or DEFAULT_CATEGORY
        balance = record_income_cat(user_id, amount, category)
        log_action(
            update,
            "income_added",
            f"amount={amount} category={category} balance={balance}",
        )
        clear_pending_state(context)
        await update.message.reply_text(
            fmt_transaction_message("income", amount, category, balance),
            parse_mode="HTML",
        )
        return

    if pending == "expense":
        amount, err = parse_amount_input(text)
        if amount is None:
            log_action(update, "expense_invalid", f"ошибка ввода: {err}")
            await update.message.reply_text(
                format_amount_error(err or "not_a_number"),
                parse_mode="HTML",
            )
            return
        category = pending_category or DEFAULT_CATEGORY
        balance = record_expense_cat(user_id, amount, category)
        log_action(
            update,
            "expense_added",
            f"amount={amount} category={category} balance={balance}",
        )
        clear_pending_state(context)
        await update.message.reply_text(
            fmt_transaction_message("expense", amount, category, balance),
            parse_mode="HTML",
        )
