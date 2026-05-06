from __future__ import annotations

import copy
import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from models import create_process_list
from validator import Validator
from algorithms.sjf import run_sjf
from algorithms.priority import run_priority
from metrics.calculator import calculate
from metrics.comparison import compare

from gui.input_panel import InputPanel
from gui.gantt_chart import GanttChartFrame

BG_DARK = "#0F1117"
BG_CARD = "#1A1D27"
BG_INPUT = "#22263A"
ACCENT_1 = "#4F8EF7"
ACCENT_2 = "#F7634F"
ACCENT_OK = "#43D9AD"
ACCENT_WARN= "#F7C948"
TEXT_PRI = "#EAEAF0"
TEXT_SEC = "#8888AA"
BORDER_CLR = "#2E3150"

FONT_TITLE = ("Consolas", 14, "bold")
FONT_HEADER = ("Consolas", 11, "bold")
FONT_BODY = ("Consolas", 10)
FONT_SMALL = ("Consolas", 9)

RESULT_COLS = [
    ("PID",       "pid",              6),
    ("Arrival",   "arrival_time",     7),
    ("Burst",     "burst_time",       6),
    ("Priority",  "priority",         8),
    ("Start",     "start_time",       6),
    ("Finish",    "completion_time",  7),
    ("WT",        "waiting_time",     5),
    ("TAT",       "turnaround_time",  5),
    ("RT",        "response_time",    5),
]


class MainWindow(tk.Tk):

    def __init__(self) -> None:
        super().__init__()
        self.title("CPU Scheduling Simulator  |  SJF vs Priority")
        self.geometry("1200x820")
        self.minsize(900, 680)
        self.configure(bg=BG_DARK)
        self._apply_styles()
        self._build_ui()

    def _apply_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(
            "TNotebook",
            background=BG_DARK,
            borderwidth=0,
            tabmargins=[0, 0, 0, 0],
        )
        style.configure(
            "TNotebook.Tab",
            background=BG_CARD,
            foreground=TEXT_SEC,
            font=FONT_BODY,
            padding=[16, 8],
            borderwidth=0,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", BG_INPUT)],
            foreground=[("selected", TEXT_PRI)],
        )

        style.configure(
            "Results.Treeview",
            background=BG_CARD,
            fieldbackground=BG_CARD,
            foreground=TEXT_PRI,
            font=FONT_BODY,
            rowheight=26,
            borderwidth=0,
        )
        style.configure(
            "Results.Treeview.Heading",
            background=BG_INPUT,
            foreground=TEXT_SEC,
            font=("Consolas", 9, "bold"),
            relief="flat",
            borderwidth=0,
        )
        style.map(
            "Results.Treeview",
            background=[("selected", ACCENT_1)],
            foreground=[("selected", BG_DARK)],
        )

        style.configure(
            "Vertical.TScrollbar",
            background=BG_CARD,
            troughcolor=BG_DARK,
            borderwidth=0,
            arrowcolor=TEXT_SEC,
        )

    def _build_ui(self) -> None:
        self._build_header()
        self._build_notebook()

    def _build_header(self) -> None:
        header = tk.Frame(self, bg=BG_CARD, pady=10)
        header.pack(fill="x")

        tk.Frame(header, bg=ACCENT_1, width=5).pack(side="left", fill="y", padx=(0, 12))

        tk.Label(
            header,
            text="CPU SCHEDULING SIMULATOR",
            font=FONT_TITLE,
            fg=TEXT_PRI, bg=BG_CARD,
        ).pack(side="left")

        tk.Label(
            header,
            text="  SJF  vs  Priority",
            font=("Consolas", 11),
            fg=TEXT_SEC, bg=BG_CARD,
        ).pack(side="left", pady=(3, 0))

        tk.Label(
            header,
            text="Operating Systems Course  ·  C4 Project",
            font=FONT_SMALL,
            fg=TEXT_SEC, bg=BG_CARD,
        ).pack(side="right", padx=16)

    def _build_notebook(self) -> None:
        self._nb = ttk.Notebook(self)
        self._nb.pack(fill="both", expand=True, padx=0, pady=0)

        self._tab_input = tk.Frame(self._nb, bg=BG_DARK)
        self._nb.add(self._tab_input, text="  ⚙  Input & Run  ")
        self._build_input_tab()

        self._tab_sjf = tk.Frame(self._nb, bg=BG_DARK)
        self._nb.add(self._tab_sjf, text="  📊  SJF Results  ")
        self._build_results_tab(
            parent=self._tab_sjf,
            algo_label="SJF – Shortest Job First (Preemptive)",
            accent=ACCENT_1,
            store_attr="sjf",
        )

        self._tab_pri = tk.Frame(self._nb, bg=BG_DARK)
        self._nb.add(self._tab_pri, text="  📊  Priority Results  ")
        self._build_results_tab(
            parent=self._tab_pri,
            algo_label="Priority Scheduling (Preemptive, lower number = higher priority)",
            accent=ACCENT_2,
            store_attr="priority",
        )

        self._tab_cmp = tk.Frame(self._nb, bg=BG_DARK)
        self._nb.add(self._tab_cmp, text="  ⚖  Comparison & Conclusion  ")
        self._build_comparison_tab()

    def _build_input_tab(self) -> None:
        banner = tk.Frame(self._tab_input, bg=BG_INPUT, pady=8)
        banner.pack(fill="x", padx=14, pady=(12, 0))

        tk.Label(
            banner,
            text=(
                "  Enter process data below, then press  RUN SIMULATION  "
                "to compare SJF and Priority Scheduling on the same workload."
            ),
            font=FONT_SMALL,
            fg=TEXT_SEC, bg=BG_INPUT,
            justify="left",
        ).pack(side="left", padx=8)

        self._input_panel = InputPanel(self._tab_input)
        self._input_panel.pack(fill="both", expand=True, padx=14, pady=(8, 0))

        run_frame = tk.Frame(self._tab_input, bg=BG_DARK, pady=10)
        run_frame.pack(fill="x", padx=14)

        self._run_btn = tk.Button(
            run_frame,
            text="▶    RUN SIMULATION",
            font=("Consolas", 12, "bold"),
            fg=BG_DARK,
            bg=ACCENT_OK,
            activeforeground=BG_DARK,
            activebackground="#38C99A",
            relief="flat",
            cursor="hand2",
            padx=28, pady=10,
            command=self._on_run,
        )
        self._run_btn.pack(side="left")

        self._status_var = tk.StringVar(value="Ready.  Enter processes and press Run.")
        self._status_lbl = tk.Label(
            run_frame,
            textvariable=self._status_var,
            font=FONT_SMALL,
            fg=TEXT_SEC, bg=BG_DARK,
        )
        self._status_lbl.pack(side="left", padx=16)

        info = tk.Frame(self._tab_input, bg=BG_CARD, pady=8, padx=12)
        info.pack(fill="x", padx=14, pady=(0, 10))

        tk.Label(
            info,
            text="Priority Rule:",
            font=("Consolas", 9, "bold"),
            fg=ACCENT_2, bg=BG_CARD,
        ).pack(side="left")

        tk.Label(
            info,
            text=(
                "  Lower number = Higher priority  (e.g. priority 1 runs before priority 5).  "
                "Ties broken by: earliest arrival time, then PID alphabetically."
            ),
            font=FONT_SMALL,
            fg=TEXT_SEC, bg=BG_CARD,
        ).pack(side="left")

    def _build_results_tab(
        self,
        parent: tk.Frame,
        algo_label: str,
        accent: str,
        store_attr: str,
    ) -> None:
        title_frame = tk.Frame(parent, bg=BG_DARK)
        title_frame.pack(fill="x", padx=14, pady=(12, 0))

        tk.Frame(title_frame, bg=accent, width=4, height=22).pack(side="left", fill="y", padx=(0, 8))
        tk.Label(
            title_frame,
            text=algo_label,
            font=FONT_HEADER,
            fg=accent, bg=BG_DARK,
        ).pack(side="left")

        gantt = GanttChartFrame(
            parent,
            title=f"{'SJF' if store_attr == 'sjf' else 'Priority'}  –  Gantt Chart",
            accent_color=accent,
        )
        gantt.pack(fill="x", padx=14, pady=(8, 0))

        tbl_label_frame = tk.Frame(parent, bg=BG_DARK)
        tbl_label_frame.pack(fill="x", padx=14, pady=(10, 2))
        tk.Label(
            tbl_label_frame,
            text="Per-Process Metrics",
            font=("Consolas", 10, "bold"),
            fg=TEXT_SEC, bg=BG_DARK,
        ).pack(side="left")

        tree_frame = tk.Frame(parent, bg=BG_DARK)
        tree_frame.pack(fill="both", expand=True, padx=14, pady=(0, 6))

        col_ids = [c[0] for c in RESULT_COLS]
        tree = ttk.Treeview(
            tree_frame,
            columns=col_ids,
            show="headings",
            style="Results.Treeview",
            height=8,
        )

        for col_label, _, width in RESULT_COLS:
            tree.heading(col_label, text=col_label)
            tree.column(col_label, width=width * 9, anchor="center", stretch=True)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        tree.pack(side="left", fill="both", expand=True)

        avg_frame = tk.Frame(parent, bg=BG_CARD, pady=6, padx=12)
        avg_frame.pack(fill="x", padx=14, pady=(0, 8))

        avg_var = tk.StringVar(value="Run the simulation to see averages.")
        tk.Label(
            avg_frame,
            textvariable=avg_var,
            font=("Consolas", 10, "bold"),
            fg=accent, bg=BG_CARD,
        ).pack(side="left")

        setattr(self, f"_{store_attr}_gantt_widget", gantt)
        setattr(self, f"_{store_attr}_tree", tree)
        setattr(self, f"_{store_attr}_avg_var", avg_var)

    def _build_comparison_tab(self) -> None:
        outer = tk.Frame(self._tab_cmp, bg=BG_DARK)
        outer.pack(fill="both", expand=True, padx=14, pady=12)

        tk.Label(
            outer,
            text="⚖  COMPARISON SUMMARY",
            font=FONT_TITLE,
            fg=TEXT_PRI, bg=BG_DARK,
        ).pack(anchor="w", pady=(0, 8))

        avg_frame = tk.Frame(outer, bg=BG_CARD, padx=8, pady=8)
        avg_frame.pack(fill="x", pady=(0, 10))

        cmp_cols = [
            ("Metric",         80),
            ("SJF",            90),
            ("Priority",       90),
            ("Winner",         90),
            ("Difference",     90),
        ]
        cmp_tree = ttk.Treeview(
            avg_frame,
            columns=[c[0] for c in cmp_cols],
            show="headings",
            style="Results.Treeview",
            height=4,
        )
        for label, w in cmp_cols:
            cmp_tree.heading(label, text=label)
            cmp_tree.column(label, width=w, anchor="center")
        cmp_tree.pack(fill="x")
        self._cmp_tree = cmp_tree

        cmp_tree.tag_configure("sjf_wins",  foreground=ACCENT_1)
        cmp_tree.tag_configure("pri_wins",  foreground=ACCENT_2)
        cmp_tree.tag_configure("tie",       foreground=ACCENT_WARN)

        fairness_frame = tk.Frame(outer, bg=BG_CARD, padx=12, pady=8)
        fairness_frame.pack(fill="x", pady=(0, 10))

        tk.Label(
            fairness_frame,
            text="Fairness / Starvation Analysis",
            font=("Consolas", 10, "bold"),
            fg=TEXT_SEC, bg=BG_CARD,
        ).pack(anchor="w")

        self._fairness_var = tk.StringVar(value="—")
        tk.Label(
            fairness_frame,
            textvariable=self._fairness_var,
            font=FONT_SMALL,
            fg=ACCENT_WARN, bg=BG_CARD,
            justify="left",
            wraplength=900,
        ).pack(anchor="w", pady=(4, 0))

        winner_frame = tk.Frame(outer, bg=BG_CARD, padx=12, pady=8)
        winner_frame.pack(fill="x", pady=(0, 10))

        tk.Label(
            winner_frame,
            text="Overall Recommendation",
            font=("Consolas", 10, "bold"),
            fg=TEXT_SEC, bg=BG_CARD,
        ).pack(anchor="w")

        self._winner_var = tk.StringVar(value="—")
        self._winner_lbl = tk.Label(
            winner_frame,
            textvariable=self._winner_var,
            font=("Consolas", 11, "bold"),
            fg=ACCENT_OK, bg=BG_CARD,
            justify="left",
            wraplength=900,
        )
        self._winner_lbl.pack(anchor="w", pady=(4, 0))

        analysis_outer = tk.Frame(outer, bg=BG_DARK)
        analysis_outer.pack(fill="both", expand=True, pady=(0, 8))

        left = tk.Frame(analysis_outer, bg=BG_DARK)
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))

        tk.Label(
            left,
            text="Analysis Summary",
            font=("Consolas", 10, "bold"),
            fg=TEXT_SEC, bg=BG_DARK,
        ).pack(anchor="w")

        self._summary_text = self._make_text_widget(left, height=10, fg=TEXT_PRI)

        right = tk.Frame(analysis_outer, bg=BG_DARK)
        right.pack(side="left", fill="both", expand=True)

        tk.Label(
            right,
            text="Conclusion",
            font=("Consolas", 10, "bold"),
            fg=TEXT_SEC, bg=BG_DARK,
        ).pack(anchor="w")

        self._conclusion_text = self._make_text_widget(right, height=10, fg=ACCENT_OK)

    def _make_text_widget(self, parent: tk.Frame, height: int, fg: str) -> tk.Text:
        frame = tk.Frame(parent, bg=BG_DARK)
        frame.pack(fill="both", expand=True)

        widget = tk.Text(
            frame,
            font=FONT_SMALL,
            fg=fg, bg=BG_CARD,
            insertbackground=TEXT_PRI,
            relief="flat",
            height=height,
            wrap="word",
            state="disabled",
            padx=8, pady=6,
        )
        vsb = ttk.Scrollbar(frame, orient="vertical", command=widget.yview)
        widget.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        widget.pack(side="left", fill="both", expand=True)
        return widget

    def _on_run(self) -> None:
        self._set_status("Running…", TEXT_SEC)

        raw_rows = self._input_panel.get_rows()

        validation = Validator.validate_all(raw_rows)
        if not validation.is_valid:
            messagebox.showerror(
                "Input Validation Error",
                validation.error_message,
                parent=self,
            )
            self._set_status(f"Validation failed: {validation.error_message}", ACCENT_2)
            return

        clean_rows: list[dict] = validation.parsed_data["processes"]

        base_processes = create_process_list(clean_rows)

        sjf_processes = copy.deepcopy(base_processes)
        priority_processes = copy.deepcopy(base_processes)

        try:
            sjf_output = run_sjf(sjf_processes)
            sjf_result = calculate(sjf_output, algorithm_name="SJF")
        except Exception as exc:
            messagebox.showerror("SJF Error", str(exc), parent=self)
            self._set_status("SJF failed.", ACCENT_2)
            return

        try:
            pri_output = run_priority(priority_processes)
            pri_result = calculate(pri_output, algorithm_name="Priority")
        except Exception as exc:
            messagebox.showerror("Priority Error", str(exc), parent=self)
            self._set_status("Priority scheduling failed.", ACCENT_2)
            return

        report = compare(sjf_result, pri_result)

        self._populate_results_tab(
            gantt_widget=self._sjf_gantt_widget,
            tree=self._sjf_tree,
            avg_var=self._sjf_avg_var,
            result=sjf_result,
            accent=ACCENT_1,
        )

        self._populate_results_tab(
            gantt_widget=self._priority_gantt_widget,
            tree=self._priority_tree,
            avg_var=self._priority_avg_var,
            result=pri_result,
            accent=ACCENT_2,
        )

        self._populate_comparison_tab(report, sjf_result, pri_result)

        self._nb.select(self._tab_sjf)
        self._set_status(
            f"Simulation complete  ·  {len(clean_rows)} processes  ·  "
            f"Overall winner: {report.overall_winner}",
            ACCENT_OK,
        )

    def _populate_results_tab(
        self,
        gantt_widget: GanttChartFrame,
        tree: ttk.Treeview,
        avg_var: tk.StringVar,
        result,
        accent: str,
    ) -> None:

        gantt_widget.render(result.gantt, result.processes)

        for item in tree.get_children():
            tree.delete(item)

        for i, proc_dict in enumerate(result.process_rows()):
            values = [proc_dict.get(key, "") for _, key, _ in RESULT_COLS]
            tag = "even" if i % 2 == 0 else "odd"
            tree.insert("", "end", values=values, tags=(tag,))

        tree.tag_configure("odd", background=BG_INPUT)
        tree.tag_configure("even", background=BG_CARD)

        avg_var.set(
            f"Averages  ─  "
            f"WT: {result.avg_waiting_time:.2f}  │  "
            f"TAT: {result.avg_turnaround_time:.2f}  │  "
            f"RT: {result.avg_response_time:.2f}"
        )

    def _populate_comparison_tab(self, report, sjf_result, pri_result) -> None:

        for item in self._cmp_tree.get_children():
            self._cmp_tree.delete(item)

        for m in report.metrics:
            if m.winner == "SJF":
                tag = "sjf_wins"
            elif m.winner == "Priority":
                tag = "pri_wins"
            else:
                tag = "tie"

            self._cmp_tree.insert(
                "", "end",
                values=(
                    m.metric_name,
                    f"{m.sjf_value:.2f}",
                    f"{m.priority_value:.2f}",
                    m.winner,
                    f"{m.difference:.2f}" if not m.is_tie else "—",
                ),
                tags=(tag,),
            )

        fairness_parts = []
        if report.starved_in_sjf:
            fairness_parts.append(
                f"⚠ SJF starvation risk – PIDs: {', '.join(report.starved_in_sjf)}"
            )
        else:
            fairness_parts.append("✔ SJF – no starvation detected")

        if report.starved_in_priority:
            fairness_parts.append(
                f"⚠ Priority starvation risk – PIDs: {', '.join(report.starved_in_priority)}"
            )
        else:
            fairness_parts.append("✔ Priority – no starvation detected")

        self._fairness_var.set("  |  ".join(fairness_parts))

        self._winner_var.set(report.recommendation)
        winner_fg = (
            ACCENT_1 if "SJF" in report.overall_winner
            else ACCENT_2 if "Priority" in report.overall_winner
            else ACCENT_WARN
        )
        self._winner_lbl.configure(fg=winner_fg)

        self._set_text(self._summary_text, "\n".join(report.summary_lines))

        self._set_text(self._conclusion_text, "\n".join(report.conclusion_lines))

    def _set_status(self, message: str, color: str = TEXT_SEC) -> None:
        self._status_var.set(message)
        self._status_lbl.configure(fg=color)

    @staticmethod
    def _set_text(widget: tk.Text, content: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("end", content)
        widget.configure(state="disabled")