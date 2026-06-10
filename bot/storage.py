"""Чтение и запись данных пользователей в JSON-файл."""

import json
import threading

from bot.config import DATA_FILE, DEFAULT_CATEGORY
from bot.logger import log_error

_store_lock = threading.Lock()


def _new_user_record() -> dict:
    return {
        "balance": 0.0,
        "income_sum": 0.0,
        "expense_sum": 0.0,
        "income_count": 0,
        "expense_count": 0,
        "income_by_category": {},
        "expense_by_category": {},
        "operations": [],
    }


def _coerce_user_record(raw: object) -> dict:
    u = _new_user_record()
    if not isinstance(raw, dict):
        return u

    u["balance"] = float(raw.get("balance", u["balance"]))
    u["income_sum"] = float(raw.get("income_sum", u["income_sum"]))
    u["expense_sum"] = float(raw.get("expense_sum", u["expense_sum"]))
    u["income_count"] = int(raw.get("income_count", u["income_count"]))
    u["expense_count"] = int(raw.get("expense_count", u["expense_count"]))

    income_by_cat = raw.get("income_by_category")
    if isinstance(income_by_cat, dict):
        u["income_by_category"] = {
            str(cat): {
                "sum": float(v.get("sum", 0.0)),
                "count": int(v.get("count", 0)),
            }
            for cat, v in income_by_cat.items()
            if isinstance(v, dict)
        }

    expense_by_cat = raw.get("expense_by_category")
    if isinstance(expense_by_cat, dict):
        u["expense_by_category"] = {
            str(cat): {
                "sum": float(v.get("sum", 0.0)),
                "count": int(v.get("count", 0)),
            }
            for cat, v in expense_by_cat.items()
            if isinstance(v, dict)
        }

    ops = raw.get("operations")
    if isinstance(ops, list):
        cleaned_ops: list[dict] = []
        for op in ops:
            if not isinstance(op, dict):
                continue
            kind = str(op.get("kind", ""))
            if kind not in ("income", "expense"):
                continue
            cleaned_ops.append(
                {
                    "kind": kind,
                    "amount": float(op.get("amount", 0.0)),
                    "category": str(op.get("category", DEFAULT_CATEGORY)),
                }
            )
        u["operations"] = cleaned_ops

    return u


def _load_users() -> dict[str, dict]:
    if not DATA_FILE.exists():
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        log_error(None, f"Не удалось прочитать {DATA_FILE}", exc)
        return {}

    users_raw = data.get("users")
    if isinstance(users_raw, dict):
        return {str(uid): _coerce_user_record(rec) for uid, rec in users_raw.items()}

    legacy = data.get("balances")
    if isinstance(legacy, dict):
        return {
            str(uid): {**_new_user_record(), "balance": float(amt)}
            for uid, amt in legacy.items()
        }

    return {}


def _save_users(users: dict[str, dict]) -> None:
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"users": users}, f, ensure_ascii=False, indent=2)
    except OSError as exc:
        log_error(None, f"Не удалось записать {DATA_FILE}", exc)
        raise


def _normalize_category(category: str | None) -> str:
    c = (category or "").strip().lower()
    return c if c else DEFAULT_CATEGORY


def _append_operation(rec: dict, kind: str, amount: float, category: str) -> None:
    ops = rec.setdefault("operations", [])
    if not isinstance(ops, list):
        ops = []
        rec["operations"] = ops
    ops.append({"kind": kind, "amount": float(amount), "category": category})


def _increment_category(by_cat: dict, category: str, amount: float) -> None:
    entry = by_cat.get(category)
    if not isinstance(entry, dict):
        entry = {"sum": 0.0, "count": 0}
        by_cat[category] = entry
    entry["sum"] = float(entry.get("sum", 0.0)) + amount
    entry["count"] = int(entry.get("count", 0)) + 1


def _decrement_category(by_cat: dict, category: str, amount: float) -> None:
    entry = by_cat.get(category)
    if not isinstance(entry, dict):
        return
    entry["sum"] = float(entry.get("sum", 0.0)) - amount
    entry["count"] = int(entry.get("count", 0)) - 1
    if entry["count"] <= 0 or entry["sum"] <= 1e-9:
        by_cat.pop(category, None)


def read_balance(user_id: int) -> float:
    with _store_lock:
        users = _load_users()
        rec = users.get(str(user_id))
        if rec is None:
            return 0.0
        return float(rec["balance"])


def record_income_cat(user_id: int, amount: float, category: str | None) -> float:
    cat = _normalize_category(category)
    with _store_lock:
        users = _load_users()
        key = str(user_id)
        rec = users.setdefault(key, _new_user_record())
        rec["balance"] = float(rec["balance"]) + amount
        rec["income_sum"] = float(rec["income_sum"]) + amount
        rec["income_count"] = int(rec["income_count"]) + 1
        _increment_category(rec.setdefault("income_by_category", {}), cat, amount)
        _append_operation(rec, "income", amount, cat)
        _save_users(users)
        return float(rec["balance"])


def record_expense_cat(user_id: int, amount: float, category: str | None) -> float:
    cat = _normalize_category(category)
    with _store_lock:
        users = _load_users()
        key = str(user_id)
        rec = users.setdefault(key, _new_user_record())
        rec["balance"] = float(rec["balance"]) - amount
        rec["expense_sum"] = float(rec["expense_sum"]) + amount
        rec["expense_count"] = int(rec["expense_count"]) + 1
        _increment_category(rec.setdefault("expense_by_category", {}), cat, amount)
        _append_operation(rec, "expense", amount, cat)
        _save_users(users)
        return float(rec["balance"])


def undo_last_operation(user_id: int) -> tuple[bool, dict | None, float]:
    with _store_lock:
        users = _load_users()
        key = str(user_id)
        rec = users.get(key)
        if rec is None:
            return False, None, 0.0

        ops = rec.get("operations")
        if not isinstance(ops, list) or not ops:
            return False, None, float(rec.get("balance", 0.0))

        last = ops.pop()
        kind = str(last.get("kind", ""))
        amount = float(last.get("amount", 0.0))
        cat = str(last.get("category", DEFAULT_CATEGORY))

        if kind == "income":
            rec["balance"] = float(rec["balance"]) - amount
            rec["income_sum"] = float(rec["income_sum"]) - amount
            rec["income_count"] = max(0, int(rec["income_count"]) - 1)
            _decrement_category(rec.setdefault("income_by_category", {}), cat, amount)
        elif kind == "expense":
            rec["balance"] = float(rec["balance"]) + amount
            rec["expense_sum"] = float(rec["expense_sum"]) - amount
            rec["expense_count"] = max(0, int(rec["expense_count"]) - 1)
            _decrement_category(rec.setdefault("expense_by_category", {}), cat, amount)
        else:
            return False, None, float(rec.get("balance", 0.0))

        _save_users(users)
        return True, last, float(rec["balance"])


def read_stats(user_id: int) -> dict:
    with _store_lock:
        users = _load_users()
        rec = users.get(str(user_id))
        if rec is None:
            return _new_user_record()
        return dict(rec)
