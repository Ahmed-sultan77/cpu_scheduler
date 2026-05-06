from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox


BG_DARK = "#0F1117"
BG_CARD = "#1A1D27"
BG_INPUT = "#22263A"
ACCENT_1 = "#4F8EF7"
ACCENT_2 = "#F7634F"
ACCENT_OK = "#43D9AD"
TEXT_PRI = "#EAEAF0"
TEXT_SEC = "#8888AA"
BORDER_CLR = "#2E3150"

FONT_HEADER = ("Consolas", 11, "bold")
FONT_BODY = ("Consolas", 10)
FONT_SMALL = ("Consolas", 9)

COLUMNS = [
    ("PID",         "pid",         7),
    ("Arrival Time", "arrival_time", 11),
    ("Burst Time",   "burst_time",   10),
    ("Priority\n(1=highest)", "priority", 11),
]

SCENARIOS: dict[str, list[dict]] = {
    "Scenario A – Basic Mixed": [
        {"pid": "P1", "arrival_time": "0",  "burst_time": "6",  "priority": "3"},
        {"pid": "P2", "arrival_time": "1",  "burst_time": "3",  "priority": "5"},
        {"pid": "P3", "arrival_time": "2",  "burst_time": "8",  "priority": "1"},
        {"pid": "P4", "arrival_time": "3",  "burst_time": "2",  "priority": "4"},
        {"pid": "P5", "arrival_time": "5",  "burst_time": "4",  "priority": "2"},
    ],
    "Scenario B – Burst vs Priority Conflict": [
        {"pid": "P1", "arrival_time": "0",  "burst_time": "2",  "priority": "5"},
        {"pid": "P2", "arrival_time": "0",  "burst_time": "10", "priority": "1"},
        {"pid": "P3", "arrival_time": "1",  "burst_time": "4",  "priority": "3"},
        {"pid": "P4", "arrival_time": "2",  "burst_time": "1",  "priority": "4"},
        {"pid": "P5", "arrival_time": "3",  "burst_time": "6",  "priority": "2"},
    ],
    "Scenario C – Starvation Risk": [
        {"pid": "P1", "arrival_time": "0",  "burst_time": "1",  "priority": "1"},
        {"pid": "P2", "arrival_time": "0",  "burst_time": "1",  "priority": "1"},
        {"pid": "P3", "arrival_time": "0",  "burst_time": "1",  "priority": "1"},
        {"pid": "P4", "arrival_time": "0",  "burst_time": "15", "priority": "5"},
        {"pid": "P5", "arrival_time": "0",  "burst_time": "12", "priority": "4"},
    ],
    "Scenario D – Validation (has error)": [
        {"pid": "P1", "arrival_time": "0",  "burst_time": "5",  "priority": "2"},
        {"pid": "P1", "arrival_time": "1",  "burst_time": "3",  "priority": "3"},
        {"pid": "P3", "arrival_time": "-1", "burst_time": "4",  "priority": "1"},
        {"pid": "P4", "arrival_time": "2",  "burst_time": "0",  "priority": "4"},
    ],
}

MAX_ROWS = 10
MIN_ROWS = 2


class InputPanel(tk.Frame):

    def __init__(self, parent: tk.Widget, **kwargs) -> None:
        super().__init__(parent, bg=BG_DARK, **kwargs)
        self._row_vars: list[dict[str, tk.StringVar]] = []
        self._entry_widgets: list[dict[str, tk.Entry]] = []
        self._build_ui()

    def _build_ui(self) -> None:
        self._build_title()
        self._build_scenario_bar()
        self._build_table_header()
        self._build_table_body()
        self._build_row_controls()

    def _build_title(self) -> None:
        title_frame = tk.Frame(self, bg=BG_DARK)
        title_frame.pack(fill="x", padx=16, pady=(14, 4))

        tk.Label(
            title_frame,
            text="⚙  PROCESS INPUT",
            font=("Consolas", 13, "bold"),
            fg=ACCENT_1, bg=BG_DARK,
        ).pack(side="left")

        tk.Label(
            title_frame,
            text=f"  (min {MIN_ROWS} · max {MAX_ROWS} processes)",
            font=FONT_SMALL,
            fg=TEXT_SEC, bg=BG_DARK,
        ).pack(side="left", pady=(2, 0))

    def _build_scenario_bar(self) -> None:
        bar = tk.Frame(self, bg=BG_DARK)
        bar.pack(fill="x", padx=16, pady=(0, 8))

        tk.Label(
            bar,
            text="Load scenario:",
            font=FONT_SMALL,
            fg=TEXT_SEC, bg=BG_DARK,
        ).pack(side="left")

        self._scenario_var = tk.StringVar(value="— choose —")
        dropdown = ttk.Combobox(
            bar,
            textvariable=self._scenario_var,
            values=list(SCENARIOS.keys()),
            state="readonly",
            width=36,
            font=FONT_SMALL,
        )
        dropdown.pack(side="left", padx=(6, 0))
        dropdown.bind("<<ComboboxSelected>>", self._on_scenario_selected)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "TCombobox",
            fieldbackground=BG_INPUT,
            background=BG_INPUT,
            foreground=TEXT_PRI,
            selectbackground=ACCENT_1,
            selectforeground=TEXT_PRI,
            arrowcolor=ACCENT_1,
        )

    def _build_table_header(self) -> None:
        header_frame = tk.Frame(self, bg=BG_CARD, pady=6)
        header_frame.pack(fill="x", padx=16)

        tk.Label(
            header_frame, text="#",
            font=FONT_SMALL, fg=TEXT_SEC, bg=BG_CARD,
            width=3, anchor="center",
        ).grid(row=0, column=0, padx=(8, 0))

        for col_idx, (label, _, width) in enumerate(COLUMNS, start=1):
            tk.Label(
                header_frame,
                text=label,
                font=FONT_SMALL,
                fg=TEXT_SEC if col_idx < 4 else ACCENT_2,
                bg=BG_CARD,
                width=width,
                anchor="center",
                justify="center",
            ).grid(row=0, column=col_idx, padx=4)

        tk.Label(
            header_frame, text="Del",
            font=FONT_SMALL, fg=TEXT_SEC, bg=BG_CARD,
            width=4,
        ).grid(row=0, column=len(COLUMNS) + 1, padx=(4, 8))

    def _build_table_body(self) -> None:
        outer = tk.Frame(self, bg=BORDER_CLR, padx=1, pady=1)
        outer.pack(fill="both", padx=16, pady=(0, 0))

        self._canvas = tk.Canvas(outer, bg=BG_CARD, highlightthickness=0, height=240)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._rows_frame = tk.Frame(self._canvas, bg=BG_CARD)
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self._rows_frame, anchor="nw"
        )

        self._rows_frame.bind("<Configure>", self._on_rows_frame_resize)
        self._canvas.bind("<Configure>", self._on_canvas_resize)

        for _ in range(3):
            self._add_row()

    def _build_row_controls(self) -> None:
        btn_frame = tk.Frame(self, bg=BG_DARK)
        btn_frame.pack(fill="x", padx=16, pady=(6, 0))

        add_btn = tk.Button(
            btn_frame,
            text="＋  Add Process",
            font=FONT_BODY,
            fg=ACCENT_OK, bg=BG_CARD,
            activeforeground=BG_DARK, activebackground=ACCENT_OK,
            relief="flat", cursor="hand2",
            padx=10, pady=4,
            command=self._add_row,
        )
        add_btn.pack(side="left")

        clear_btn = tk.Button(
            btn_frame,
            text="✕  Clear All",
            font=FONT_BODY,
            fg=ACCENT_2, bg=BG_CARD,
            activeforeground=BG_DARK, activebackground=ACCENT_2,
            relief="flat", cursor="hand2",
            padx=10, pady=4,
            command=self.clear,
        )
        clear_btn.pack(side="left", padx=(8, 0))

    def _add_row(self, preset: dict | None = None) -> None:
        if len(self._row_vars) >= MAX_ROWS:
            messagebox.showwarning(
                "Limit Reached",
                f"Maximum {MAX_ROWS} processes allowed.",
                parent=self,
            )
            return

        row_idx = len(self._row_vars)
        vars_dict: dict[str, tk.StringVar] = {}
        entries_dict: dict[str, tk.Entry] = {}

        row_frame = tk.Frame(self._rows_frame, bg=BG_CARD)
        row_frame.pack(fill="x", padx=0, pady=1)

        row_bg = BG_CARD if row_idx % 2 == 0 else BG_INPUT
        row_frame.configure(bg=row_bg)

        tk.Label(
            row_frame,
            text=str(row_idx + 1),
            font=FONT_SMALL, fg=TEXT_SEC, bg=row_bg,
            width=3, anchor="center",
        ).grid(row=0, column=0, padx=(8, 0), pady=4)

        for col_idx, (_, key, width) in enumerate(COLUMNS, start=1):
            var = tk.StringVar(value=preset.get(key, "") if preset else "")
            vars_dict[key] = var

            entry_bg = BG_INPUT
            entry_fg = ACCENT_2 if key == "priority" else TEXT_PRI

            entry = tk.Entry(
                row_frame,
                textvariable=var,
                font=FONT_BODY,
                fg=entry_fg, bg=entry_bg,
                insertbackground=TEXT_PRI,
                relief="flat",
                width=width,
                justify="center",
            )
            entry.grid(row=0, column=col_idx, padx=4, pady=4)
            entries_dict[key] = entry

            entry.bind("<Tab>", lambda e, f=row_frame: f.tk_focusNext().focus())

        del_btn = tk.Button(
            row_frame,
            text="✕",
            font=("Consolas", 9, "bold"),
            fg=ACCENT_2, bg=row_bg,
            activeforeground=BG_DARK, activebackground=ACCENT_2,
            relief="flat", cursor="hand2",
            width=3,
            command=lambda rf=row_frame, vd =vars_dict:  self._delete_row(rf, vd),
        )
        del_btn.grid(row=0, column=len(COLUMNS) + 1, padx=(4, 8))

        self._row_vars.append(vars_dict)
        self._entry_widgets.append(entries_dict)
        self._update_scroll()

    def _delete_row(self, row_frame: tk.Frame, vars_dict: dict) -> None:
        if len(self._row_vars) <= MIN_ROWS:
            messagebox.showwarning(
                "Minimum Rows",
                f"You need at least {MIN_ROWS} processes.",
                parent=self,
            )
            return
        
        idx = self._row_vars.index(vars_dict)
        row_frame.destroy()

        del self._row_vars[idx]
        del self._entry_widgets[idx]

        self._refresh_row_numbers()
        self._update_scroll()

    def _refresh_row_numbers(self) -> None:
        for i, child in enumerate(self._rows_frame.winfo_children()):
            labels = [w for w in child.winfo_children() if isinstance(w, tk.Label)]
            if labels:
                labels[0].configure(text=str(i + 1))

    def get_rows(self) -> list[dict]:
        return [
            {key: var.get().strip() for key, var in row.items()}
            for row in self._row_vars
        ]

    def clear(self) -> None:
        for child in self._rows_frame.winfo_children():
            child.destroy()
        self._row_vars.clear()
        self._entry_widgets.clear()
        self._scenario_var.set("— choose —")
        for _ in range(MIN_ROWS):
            self._add_row()

    def load_scenario(self, name: str) -> None:
        preset_rows = SCENARIOS.get(name)
        if preset_rows is None:
            return

        for child in self._rows_frame.winfo_children():
            child.destroy()
        self._row_vars.clear()
        self._entry_widgets.clear()

        for preset in preset_rows:
            self._add_row(preset=preset)

    def _on_scenario_selected(self, _event: tk.Event) -> None:
        name = self._scenario_var.get()
        if name.startswith("—"):
            return
        self.load_scenario(name)

    def _on_rows_frame_resize(self, _event: tk.Event) -> None:
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_resize(self, event: tk.Event) -> None:
        self._canvas.itemconfig(self._canvas_window, width=event.width)

    def _update_scroll(self) -> None:
        self._rows_frame.update_idletasks()
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))