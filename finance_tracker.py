import tkinter as tk
from tkinter import ttk, messagebox
import json
import shutil
from datetime import datetime
from pathlib import Path


class FinanceTrackerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Финансовый трекер")
        self.root.geometry("700x500")
        self.root.minsize(650, 450)
        self.root.resizable(True, True)
        # Общий, читаемый шрифт для всех элементов (Windows: Segoe UI обычно доступен)
        try:
            self.root.option_add("*Font", ("Segoe UI", 10))
        except tk.TclError:
            pass

        style = ttk.Style(self.root)
        # Тема влияет на "приятность" отрисовки виджетов ttk
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10), padding=(10, 5))
        style.configure("TEntry", padding=(6, 3))
        style.configure("TCombobox", padding=(6, 3))
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=24)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

        self.data_file = Path(__file__).with_name("finance_data.json")
        # Папка для резервных копий: рядом с finance_data.json
        self.backup_dir = Path(__file__).with_name("finance_backups")
        self.operations = []
        self.next_operation_id = 1
        self.balance = 0.0
        self._create_widgets()
        self._load_data()

    def _create_widgets(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=0)
        self.root.rowconfigure(1, weight=1)
        self.root.rowconfigure(2, weight=0)

        input_frame = ttk.LabelFrame(self.root, text="Новая операция", padding=10)
        input_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        input_frame.columnconfigure(0, weight=0)
        input_frame.columnconfigure(1, weight=1)
        input_frame.columnconfigure(2, weight=0)
        input_frame.columnconfigure(3, weight=1)

        ttk.Label(input_frame, text="Сумма:").grid(row=0, column=0, sticky="w")
        self.amount_var = tk.StringVar()
        amount_entry = ttk.Entry(input_frame, textvariable=self.amount_var, width=20)
        amount_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(input_frame, text="Описание:").grid(row=0, column=2, sticky="w")
        self.desc_var = tk.StringVar()
        desc_entry = ttk.Entry(input_frame, textvariable=self.desc_var, width=35)
        desc_entry.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        income_btn = ttk.Button(
            input_frame,
            text="Добавить доход",
            command=lambda: self.add_operation("Доход"),
        )
        income_btn.grid(row=1, column=1, pady=8, sticky="ew")

        expense_btn = ttk.Button(
            input_frame,
            text="Добавить расход",
            command=lambda: self.add_operation("Расход"),
        )
        expense_btn.grid(row=1, column=3, pady=8, sticky="ew")

        delete_btn = ttk.Button(
            input_frame,
            text="Удалить выбранную запись",
            command=self.delete_selected_operation,
        )
        delete_btn.grid(row=2, column=1, columnspan=3, pady=4, sticky="ew")

        ttk.Label(input_frame, text="Фильтр:").grid(row=3, column=0, sticky="w", pady=4)
        self.filter_var = tk.StringVar(value="Все")
        filter_box = ttk.Combobox(
            input_frame,
            textvariable=self.filter_var,
            values=("Все", "Доходы", "Расходы"),
            state="readonly",
            width=20,
        )
        filter_box.grid(row=3, column=1, sticky="ew", padx=5, pady=4)
        filter_box.bind("<<ComboboxSelected>>", self._on_filter_changed)

        operations_frame = ttk.LabelFrame(self.root, text="Список операций", padding=10)
        operations_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        operations_frame.rowconfigure(0, weight=1)
        operations_frame.columnconfigure(0, weight=1)
        operations_frame.columnconfigure(1, weight=0)

        columns = ("type", "amount", "description")
        self.tree = ttk.Treeview(operations_frame, columns=columns, show="headings")
        self.tree.heading("type", text="Тип")
        self.tree.heading("amount", text="Сумма")
        self.tree.heading("description", text="Описание")

        self.tree.column("type", width=100, anchor="center")
        self.tree.column("amount", width=120, anchor="e")
        self.tree.column("description", width=420, anchor="w")
        self.tree.tag_configure("income", foreground="green")
        self.tree.tag_configure("expense", foreground="red")

        scrollbar = ttk.Scrollbar(operations_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=2)
        scrollbar.grid(row=0, column=1, sticky="ns", pady=2)

        balance_frame = ttk.Frame(self.root, padding=10)
        balance_frame.grid(row=2, column=0, sticky="ew")
        balance_frame.columnconfigure(0, weight=1)
        balance_frame.columnconfigure(1, weight=0)

        ttk.Label(
            balance_frame,
            text="Общий баланс:",
            font=("Segoe UI", 11, "bold"),
        ).grid(row=0, column=0, sticky="w")
        self.balance_var = tk.StringVar(value="0.00 ₽")
        self.balance_label = ttk.Label(
            balance_frame,
            textvariable=self.balance_var,
            font=("Segoe UI", 11, "bold"),
        )
        self.balance_label.grid(row=0, column=1, sticky="e", padx=(10, 0))

    def add_operation(self, op_type: str) -> None:
        amount_text = self.amount_var.get().strip().replace(",", ".")
        description = self.desc_var.get().strip()

        if not amount_text:
            messagebox.showwarning("Ошибка ввода", "Введите сумму.")
            return

        try:
            amount = float(amount_text)
        except ValueError:
            messagebox.showerror("Ошибка ввода", "Сумма должна быть числом.")
            return

        if amount <= 0:
            messagebox.showwarning("Ошибка ввода", "Сумма должна быть больше нуля.")
            return

        if not description:
            description = "Без описания"

        signed_amount = amount if op_type == "Доход" else -amount
        operation = {
            "id": self.next_operation_id,
            "type": op_type,
            "amount": signed_amount,
            "description": description,
        }
        self.next_operation_id += 1
        self.operations.append(operation)
        self.balance += signed_amount

        self._refresh_operations_view()
        self._update_balance_label()
        self._save_data()

        self.amount_var.set("")
        self.desc_var.set("")

    def _update_balance_label(self) -> None:
        self.balance_var.set(f"{self.balance:.2f} ₽")

        if self.balance > 0:
            color = "green"
        elif self.balance < 0:
            color = "red"
        else:
            color = "black"

        self.balance_label.configure(foreground=color)

    def _backup_data(self) -> None:
        """
        Создает резервную копию файла finance_data.json перед сохранением.
        Новые копии кладутся в папку finance_backups рядом с основным файлом.
        """
        if not self.data_file.exists():
            return

        try:
            self.backup_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"finance_data_{timestamp}.json"
            backup_path = self.backup_dir / backup_name
            shutil.copy2(self.data_file, backup_path)
        except OSError:
            # Резервное копирование не должно мешать основной работе,
            # поэтому просто показываем предупреждение и продолжаем.
            messagebox.showwarning(
                "Резервное копирование",
                "Не удалось создать резервную копию данных.\n"
                "Основной файл будет сохранен без копии.",
            )

    def _save_data(self) -> None:
        data = {"operations": self.operations, "next_operation_id": self.next_operation_id}
        try:
            # Сначала создаем резервную копию существующего файла
            self._backup_data()
            # Затем сохраняем новые данные
            self.data_file.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError:
            messagebox.showerror(
                "Ошибка сохранения",
                "Не удалось сохранить данные в файл.",
            )

    def _load_data(self) -> None:
        if not self.data_file.exists():
            return

        try:
            raw_data = self.data_file.read_text(encoding="utf-8")
            data = json.loads(raw_data)
        except (OSError, json.JSONDecodeError):
            messagebox.showwarning(
                "Ошибка загрузки",
                "Файл данных поврежден или недоступен. Начинаем с пустого списка.",
            )
            return

        operations = data.get("operations", [])
        if not isinstance(operations, list):
            return

        self.operations = []
        self.balance = 0.0
        loaded_max_id = 0
        for op in operations:
            if not isinstance(op, dict):
                continue

            op_id = op.get("id")
            op_type = op.get("type")
            amount = op.get("amount")
            description = op.get("description", "Без описания")

            if op_type not in ("Доход", "Расход"):
                continue
            if not isinstance(amount, (int, float)):
                continue
            if not isinstance(op_id, int) or op_id <= 0:
                op_id = loaded_max_id + 1
            if not isinstance(description, str):
                description = "Без описания"

            signed_amount = float(amount)
            loaded_max_id = max(loaded_max_id, op_id)
            self.operations.append(
                {
                    "id": op_id,
                    "type": op_type,
                    "amount": signed_amount,
                    "description": description,
                }
            )
            self.balance += signed_amount

        saved_next_id = data.get("next_operation_id")
        if isinstance(saved_next_id, int) and saved_next_id > loaded_max_id:
            self.next_operation_id = saved_next_id
        else:
            self.next_operation_id = loaded_max_id + 1

        self._refresh_operations_view()
        self._update_balance_label()

    def delete_selected_operation(self) -> None:
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showinfo("Удаление", "Выберите запись для удаления.")
            return

        item_id = selected_item[0]
        try:
            selected_operation_id = int(item_id)
        except ValueError:
            messagebox.showerror("Ошибка", "Не удалось определить выбранную запись.")
            return

        remove_index = None
        for index, op in enumerate(self.operations):
            if op.get("id") == selected_operation_id:
                remove_index = index
                break

        if remove_index is None:
            messagebox.showerror("Ошибка", "Не удалось найти запись для удаления.")
            return

        removed_operation = self.operations.pop(remove_index)
        removed_amount = float(removed_operation.get("amount", 0.0))
        self.balance -= removed_amount

        self._refresh_operations_view()
        self._update_balance_label()
        self._save_data()

    def _on_filter_changed(self, _event: object) -> None:
        self._refresh_operations_view()

    def _operation_matches_filter(self, operation: dict) -> bool:
        current_filter = self.filter_var.get()
        if current_filter == "Доходы":
            return operation.get("type") == "Доход"
        if current_filter == "Расходы":
            return operation.get("type") == "Расход"
        return True

    def _refresh_operations_view(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        for operation in self.operations:
            if not self._operation_matches_filter(operation):
                continue

            amount = float(operation.get("amount", 0.0))
            amount_display = f"{amount:+.2f} ₽"
            op_type = operation.get("type", "")
            row_tag = "income" if op_type == "Доход" else "expense"
            self.tree.insert(
                "",
                "end",
                iid=str(operation.get("id")),
                values=(
                    op_type,
                    amount_display,
                    operation.get("description", "Без описания"),
                ),
                tags=(row_tag,),
            )


def main() -> None:
    root = tk.Tk()
    app = FinanceTrackerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
