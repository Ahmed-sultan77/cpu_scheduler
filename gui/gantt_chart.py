from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

import matplotlib
matplotlib.use("TkAgg") 
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

BG_DARK = "#0F1117"
BG_CARD = "#1A1D27"
BG_CHART = "#12151F"
TEXT_PRI = "#EAEAF0"
TEXT_SEC = "#8888AA"
BORDER_CLR = "#2E3150"
IDLE_COLOR = "#3A3F5C"

PROCESS_COLORS = [
    "#4F8EF7",
    "#43D9AD",
    "#F7634F",
    "#F7C948",
    "#A78BFA",
    "#FB7185",
    "#34D399",
    "#60A5FA",
    "#F472B6",
    "#FBBF24",
]

FONT_HEADER = ("Consolas", 11, "bold")
FONT_BODY = ("Consolas", 10)
FONT_SMALL = ("Consolas", 9)


class GanttChartFrame(tk.Frame):

    def __init__(
        self,
        parent: tk.Widget,
        title: str,
        accent_color: str,
        **kwargs,
    ) -> None:
        super().__init__(parent, bg=BG_DARK, **kwargs)
        self._title        = title
        self._accent_color = accent_color
        self._figure: plt.Figure | None = None
        self._canvas_widget: FigureCanvasTkAgg | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        stripe = tk.Frame(self, bg=self._accent_color, height=3)
        stripe.pack(fill="x")

        tk.Label(
            self,
            text=self._title,
            font=FONT_HEADER,
            fg=self._accent_color,
            bg=BG_DARK,
            pady=6,
        ).pack(anchor="w", padx=14)

        self._placeholder = tk.Label(
            self,
            text="Chart will appear here after running the simulation.",
            font=FONT_SMALL,
            fg=TEXT_SEC,
            bg=BG_DARK,
        )
        self._placeholder.pack(expand=True, pady=20)

        self._chart_container = tk.Frame(self, bg=BG_DARK)
        self._chart_container.pack(fill="both", expand=True, padx=6, pady=(0, 6))

    def render(self, gantt_entries: list, processes: list) -> None:
        self._placeholder.pack_forget()
        self._destroy_previous_figure()

        pids = [p.pid for p in processes]
        color_map: dict[str, str] = {}
        for i, pid in enumerate(pids):
            color_map[pid] = PROCESS_COLORS[i % len(PROCESS_COLORS)]

        fig_height = max(2.2, 1.0 + 0.45 * len(pids))
        fig, ax = plt.subplots(figsize=(9, fig_height))
        fig.patch.set_facecolor(BG_CHART)
        ax.set_facecolor(BG_CHART)

        bar_height = 0.55
        y_pos = 0.5 

        time_labels: list[int] = []

        for entry in gantt_entries:
            duration = entry.end - entry.start
            color = IDLE_COLOR if entry.pid == "idle" else color_map.get(entry.pid, IDLE_COLOR)
            label = "Idle" if entry.pid == "idle" else entry.pid

            bar = mpatches.FancyBboxPatch(
                (entry.start, y_pos - bar_height / 2),
                duration,
                bar_height,
                boxstyle="round,pad=0.03",
                facecolor=color,
                edgecolor=BG_CHART,
                linewidth=1.2,
                zorder=2,
            )
            ax.add_patch(bar)

            if duration >= 1:
                ax.text(
                    entry.start + duration / 2,
                    y_pos,
                    label,
                    ha="center", va="center",
                    fontsize=9, fontweight="bold",
                    color="#FFFFFF" if entry.pid != "idle" else TEXT_SEC,
                    zorder=3,
                )

            time_labels.append(entry.start)

        if gantt_entries:
            time_labels.append(gantt_entries[-1].end)

        unique_times = sorted(set(time_labels))
        ax.set_xticks(unique_times)
        ax.set_xticklabels(
            [str(t) for t in unique_times],
            color=TEXT_SEC, fontsize=8,
        )

        for t in unique_times:
            ax.axvline(x=t, color=BORDER_CLR, linewidth=0.8, zorder=1, linestyle="--", alpha=0.5)

        legend_patches = [
            mpatches.Patch(facecolor=color_map[pid], label=pid, edgecolor="none")
            for pid in pids
        ]
        if any(e.pid == "idle" for e in gantt_entries):
            legend_patches.append(
                mpatches.Patch(facecolor=IDLE_COLOR, label="Idle", edgecolor="none")
            )

        ax.legend(
            handles=legend_patches,
            loc="upper right",
            fontsize=8,
            framealpha=0.15,
            labelcolor=TEXT_PRI,
            facecolor=BG_CARD,
            edgecolor=BORDER_CLR,
        )

        max_time = gantt_entries[-1].end if gantt_entries else 1
        ax.set_xlim(gantt_entries[0].start if gantt_entries else 0, max_time + 0.2)
        ax.set_ylim(0, 1)
        ax.set_yticks([])
        ax.set_xlabel("Time (units)", color=TEXT_SEC, fontsize=9)

        for spine in ax.spines.values():
            spine.set_color(BORDER_CLR)

        ax.tick_params(axis="x", colors=TEXT_SEC, length=4)

        fig.tight_layout(pad=0.8)

        self._figure = fig
        self._canvas_widget = FigureCanvasTkAgg(fig, master=self._chart_container)
        self._canvas_widget.draw()
        self._canvas_widget.get_tk_widget().pack(fill="both", expand=True)

    def clear(self) -> None:
        self._destroy_previous_figure()
        self._placeholder.pack(expand=True, pady=20)

    def _destroy_previous_figure(self) -> None:
        if self._canvas_widget is not None:
            self._canvas_widget.get_tk_widget().destroy()
            self._canvas_widget = None
        if self._figure is not None:
            plt.close(self._figure)
            self._figure = None