import tkinter as tk
import re
import math


class Calculator:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Калькулятор")
        self.root.resizable(False, False)
        self.root.configure(bg="#1f2430")

        self.expression = ""
        self.display_var = tk.StringVar(value="0")

        self._create_ui()
        self._bind_keyboard()
        self._fit_window_to_content()

    def _create_ui(self) -> None:
        container = tk.Frame(self.root, bg="#1f2430", padx=10, pady=10)
        container.grid(row=0, column=0, sticky="nsew")

        display = tk.Entry(
            container,
            textvariable=self.display_var,
            font=("Segoe UI", 24, "bold"),
            justify="right",
            bd=0,
            relief="flat",
            state="readonly",
            readonlybackground="#2d3446",
            fg="#f8f8f2",
            insertbackground="#f8f8f2",
        )
        display.grid(row=0, column=0, columnspan=4, sticky="nsew", pady=(0, 10), ipady=12)

        buttons = [
            ("7", 1, 0),
            ("8", 1, 1),
            ("9", 1, 2),
            ("/", 1, 3),
            ("4", 2, 0),
            ("5", 2, 1),
            ("6", 2, 2),
            ("*", 2, 3),
            ("1", 3, 0),
            ("2", 3, 1),
            ("3", 3, 2),
            ("-", 3, 3),
            ("0", 4, 0),
            (".", 4, 1),
            ("=", 4, 2),
            ("+", 4, 3),
            ("±", 5, 0),
            ("⌫", 5, 1),
            ("C", 5, 2),
            ("√", 5, 3),
        ]

        operators = {"+", "-", "*", "/", "=", "√"}
        controls = {"C", "⌫", "±"}

        for text, row, col in buttons:
            if text in operators:
                bg, active_bg, fg = "#e74c3c", "#ff6b5d", "#ffffff"
            elif text in controls:
                bg, active_bg, fg = "#2ecc71", "#4be08c", "#0d2b17"
            else:
                bg, active_bg, fg = "#2d3446", "#3a435a", "#ffffff"

            btn = tk.Button(
                container,
                text=text,
                font=("Segoe UI", 14, "bold"),
                bg=bg,
                fg=fg,
                activebackground=active_bg,
                activeforeground=fg,
                bd=0,
                relief="flat",
                cursor="hand2",
                command=lambda t=text: self.on_button_click(t),
            )
            btn.grid(row=row, column=col, sticky="nsew", padx=4, pady=4, ipady=10)

        for i in range(6):
            container.grid_rowconfigure(i, weight=1)
        for i in range(4):
            container.grid_columnconfigure(i, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

    def _fit_window_to_content(self) -> None:
        self.root.update_idletasks()
        req_width = self.root.winfo_reqwidth()
        req_height = self.root.winfo_reqheight()
        self.root.geometry(f"{req_width}x{req_height}")

    def _bind_keyboard(self) -> None:
        self.root.bind("<Key>", self.on_key_press)
        self.root.focus_set()

    def on_key_press(self, event: tk.Event) -> None:
        key = event.keysym
        char = event.char

        if char in "0123456789+-*/.":
            self.on_button_click(char)
            return

        if char == ",":
            self.on_button_click(".")
            return

        if key in ("Return", "KP_Enter"):
            self.on_button_click("=")
            return

        if key == "BackSpace":
            self.on_button_click("⌫")
            return

        if key in ("Escape", "Delete"):
            self.on_button_click("C")
            return

    def on_button_click(self, value: str) -> None:
        if value == "C":
            self.expression = ""
            self.display_var.set("0")
            return

        if value == "=":
            self.calculate_result()
            return

        if value == "⌫":
            self.backspace()
            return

        if value == "±":
            self.toggle_sign()
            return

        if value == "√":
            self.sqrt_result()
            return

        self.expression += value
        self.display_var.set(self.expression)

    def backspace(self) -> None:
        if not self.expression:
            return
        self.expression = self.expression[:-1]
        self.display_var.set(self.expression if self.expression else "0")

    def toggle_sign(self) -> None:
        if not self.expression:
            self.expression = "-"
            self.display_var.set(self.expression)
            return

        # Меняем знак только у последнего числа в выражении.
        match = re.search(r"(\d+\.?\d*|\.\d+)$", self.expression)
        if not match:
            return

        start, end = match.span()
        number = self.expression[start:end]

        if start > 0 and self.expression[start - 1] == "-":
            if start - 1 == 0 or self.expression[start - 2] in "+-*/":
                self.expression = self.expression[: start - 1] + number + self.expression[end:]
                self.display_var.set(self.expression if self.expression else "0")
                return

        self.expression = self.expression[:start] + "-" + number + self.expression[end:]
        self.display_var.set(self.expression)

    def calculate_result(self) -> None:
        try:
            result = eval(self.expression)
            self.expression = str(result)
            self.display_var.set(self.expression)
        except ZeroDivisionError:
            self.expression = ""
            self.display_var.set("Ошибка: деление на 0")
        except Exception:
            self.expression = ""
            self.display_var.set("Ошибка")

    def sqrt_result(self) -> None:
        if not self.expression:
            return

        try:
            value = eval(self.expression)
            if value < 0:
                self.expression = ""
                self.display_var.set("Ошибка: корень < 0")
                return

            result = math.sqrt(value)
            self.expression = str(result)
            self.display_var.set(self.expression)
        except Exception:
            self.expression = ""
            self.display_var.set("Ошибка")


def main() -> None:
    root = tk.Tk()
    Calculator(root)
    root.mainloop()


if __name__ == "__main__":
    main()
