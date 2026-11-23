"""
students_tab.py — Student management tab (Phase 2, Tasks 2.1 & 2.2).

Features:
• Full student list with columns: Name, RFID, Sections
• Real-time search box (filters by name or card ID)
• Sortable columns (click header → toggle asc/desc)
• Add / Edit / Delete buttons per row  +  top-level Add button
• Delegates all data mutations to student_controller
"""

from __future__ import annotations

from typing import Any, Optional

import customtkinter as ctk
from tkinter import messagebox

import controllers.student_controller as student_ctrl
import controllers.attendance_controller as attendance_ctrl
from views.dialogs.student_edit_dialog import StudentEditDialog
from views.dialogs.manual_attendance_dialog import ManualAttendanceDialog
from utils.logger import log_info, log_warning
from utils.localization import turkish_lower


# Column definitions: (header label, dict key, display width)
_COLUMNS: list[tuple[str, str, int]] = [
    ("Name",         "full_name",      190),
    ("RFID",         "card_id",        140),
    ("Sections",     "sections",       190),
    ("Attendance %", "attendance_pct",  90),
]


class StudentsTab(ctk.CTkFrame):
    """Students management tab — fully implemented in Phase 2."""

    _PAGE_SIZE = 20  # Rows rendered per page for performance

    def __init__(self, parent: Any, root: Any) -> None:
        super().__init__(parent, fg_color="#1a1a2e", corner_radius=0)
        self._app = root

        self._all_rows: list[dict] = []       # full data from controller
        self._display_rows: list[dict] = []   # after search + sort
        self._visible_count: int = 0          # how many rows currently rendered

        self._selected_ids: set[int] = set()
        self._risk: dict[int, str] = {}
        self._row_checks: dict[int, ctk.CTkCheckBox] = {}
        self._sort_key: str = "full_name"
        self._sort_asc: bool = True
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", self._on_search_change)
        self._search_debounce_id: Optional[str] = None

        self._build_ui()
        self._load()

    # ──────────────────────────────────────────────────────────────────────────
    # UI construction
    # ──────────────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # ── Header row ────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(18, 8))

        ctk.CTkLabel(
            hdr, text="Students",
            font=ctk.CTkFont(size=26, weight="bold"), text_color="#e0e0e0",
        ).pack(side="left")

        ctk.CTkButton(
            hdr, text="+ Add Student", width=150, height=40,
            fg_color="#2563eb", hover_color="#1d4ed8",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._add_student,
        ).pack(side="right", padx=4)

        # ── Search bar ────────────────────────────────────────────────────────
        search_frame = ctk.CTkFrame(self, fg_color="#0f0f23", corner_radius=8)
        search_frame.pack(fill="x", padx=24, pady=(0, 8))

        ctk.CTkLabel(
            search_frame, text="🔍", font=ctk.CTkFont(size=14), text_color="#6b7280",
        ).pack(side="left", padx=(12, 4), pady=6)

        self._search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self._search_var,
            placeholder_text="Search by name or card ID…",
            width=400, height=36,
            font=ctk.CTkFont(size=13),
            fg_color="transparent",
            border_width=0,
        )
        self._search_entry.pack(side="left", padx=(0, 12), pady=4)

        self._count_label = ctk.CTkLabel(
            search_frame, text="",
            font=ctk.CTkFont(size=12), text_color="#6b7280",
        )
        self._count_label.pack(side="right", padx=16)

        # ── Filter bar ────────────────────────────────────────────────────────
        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.pack(fill="x", padx=24, pady=(0, 6))

        ctk.CTkLabel(
            filter_frame, text="Section:", font=ctk.CTkFont(size=12),
            text_color="#9ca3af",
        ).pack(side="left", padx=(0, 4))

        self._section_filter_var = ctk.StringVar(value="All Sections")
        self._section_filter = ctk.CTkComboBox(
            filter_frame, variable=self._section_filter_var,
            values=["All Sections"], width=180, height=30,
            font=ctk.CTkFont(size=12), state="readonly",
            command=lambda _v: self._apply_filter(),
        )
        self._section_filter.pack(side="left", padx=(0, 16))

        self._hide_inactive_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            filter_frame, text="Hide inactive students",
            variable=self._hide_inactive_var,
            font=ctk.CTkFont(size=12), height=28,
            command=self._apply_filter,
        ).pack(side="left")

        ctk.CTkLabel(
            filter_frame,
            text="  🟢 sorun yok   🟡 riskli   🔴 2 üst üste veya 3 toplam devamsızlık",
            font=ctk.CTkFont(size=11), text_color="#9ca3af",
        ).pack(side="left", padx=(16, 0))

        self._delete_sel_btn = ctk.CTkButton(
            filter_frame, text="Delete Selected (0)", width=170, height=30,
            fg_color="#7f1d1d", hover_color="#991b1b",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._delete_selected,
        )
        self._delete_sel_btn.pack(side="right")

        self._select_all_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            filter_frame, text="Select all (filtered)",
            variable=self._select_all_var,
            font=ctk.CTkFont(size=12), height=28,
            command=self._toggle_select_all,
        ).pack(side="right", padx=(0, 16))

        # ── Column headers ────────────────────────────────────────────────────
        self._col_hdr = ctk.CTkFrame(self, fg_color="#0f0f23", corner_radius=0)
        self._col_hdr.pack(fill="x", padx=24)
        self._col_buttons: dict[str, ctk.CTkButton] = {}

        ctk.CTkLabel(self._col_hdr, text="", width=30).pack(side="left", padx=(12, 0))
        for label, key, width in _COLUMNS:
            btn = ctk.CTkButton(
                self._col_hdr,
                text=label,
                width=width,
                height=32,
                fg_color="transparent",
                hover_color="#1e293b",
                text_color="#a0aec0",
                font=ctk.CTkFont(size=12, weight="bold"),
                anchor="w",
                command=lambda k=key: self._sort_by(k),
            )
            btn.pack(side="left", padx=4, pady=4)
            self._col_buttons[key] = btn

        # Spacer for action buttons column
        ctk.CTkLabel(
            self._col_hdr, text="", width=250,
        ).pack(side="left", padx=4)

        # ── Scrollable list ───────────────────────────────────────────────────
        self._list_frame = ctk.CTkScrollableFrame(
            self, fg_color="#111125", corner_radius=0,
        )
        self._list_frame.pack(fill="both", expand=True, padx=24, pady=(0, 24))

    # ──────────────────────────────────────────────────────────────────────────
    # Data loading + filtering
    # ──────────────────────────────────────────────────────────────────────────

    def _load(self) -> None:
        """Reload all students from DB and re-render."""
        try:
            raw = student_ctrl.get_all_students_with_sections()
        except Exception as exc:
            log_warning(f"StudentsTab: failed to load students — {exc}")
            messagebox.showerror("Error", f"Could not load students:\n{exc}", parent=self._app)
            return

        # Add a combined 'full_name' key for sorting/display
        for row in raw:
            row["full_name"] = f"{row['first_name']} {row['last_name']}"

        self._all_rows = raw

        # Refresh section filter options
        section_names = sorted({
            s.strip()
            for r in raw if r.get("sections")
            for s in r["sections"].split(",")
        })
        self._section_filter.configure(values=["All Sections"] + section_names)

        self._selected_ids &= {r["id"] for r in raw}
        try:
            self._risk = attendance_ctrl.get_student_risk_levels()
        except Exception as exc:
            log_warning(f"StudentsTab: risk levels failed — {exc}")
            self._risk = {}
        self._apply_filter()
        self._update_delete_btn()

    def _apply_filter(self) -> None:
        """Apply current search query + section filter + inactive filter + sort, then re-render."""
        query = turkish_lower(self._search_var.get().strip())
        sec_filter = self._section_filter_var.get()
        hide_inactive = self._hide_inactive_var.get()

        filtered = list(self._all_rows)

        # Section filter
        if sec_filter and sec_filter != "All Sections":
            filtered = [
                r for r in filtered
                if sec_filter in [s.strip() for s in r.get("sections", "").split(",")]
            ]

        # Inactive filter
        if hide_inactive:
            filtered = [r for r in filtered if not r.get("is_inactive")]

        # Text search
        if query:
            filtered = [
                r for r in filtered
                if query in turkish_lower(r["full_name"])
                or query in turkish_lower(r["card_id"])
                or query in turkish_lower(r["sections"])
            ]

        # Sort
        filtered.sort(
            key=lambda r: turkish_lower(str(r.get(self._sort_key, ""))),
            reverse=not self._sort_asc,
        )

        self._display_rows = filtered
        self._render_rows()
        self._update_sort_indicators()
        self._count_label.configure(
            text=f"{len(filtered)} of {len(self._all_rows)} student(s)"
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Rendering
    # ──────────────────────────────────────────────────────────────────────────

    def _render_rows(self) -> None:
        for w in self._list_frame.winfo_children():
            w.destroy()
        self._visible_count = 0
        self._row_checks.clear()

        if not self._display_rows:
            ctk.CTkLabel(
                self._list_frame,
                text="No students found." if self._all_rows else
                     "No students yet. Click '+ Add Student' to get started.",
                font=ctk.CTkFont(size=14), text_color="#6b7280",
            ).pack(pady=40)
            return

        # Render first page
        self._render_page()

    def _render_page(self) -> None:
        """Render the next batch of rows (pagination)."""
        start = self._visible_count
        end = min(start + self._PAGE_SIZE, len(self._display_rows))
        for row_data in self._display_rows[start:end]:
            self._render_row(row_data)
        self._visible_count = end

        # Remove existing "Load More" button if present
        if hasattr(self, "_load_more_btn") and self._load_more_btn is not None:
            try:
                self._load_more_btn.destroy()
            except Exception:
                pass
            self._load_more_btn = None

        # Add "Load More" button if there are more rows
        if self._visible_count < len(self._display_rows):
            remaining = len(self._display_rows) - self._visible_count
            self._load_more_btn = ctk.CTkButton(
                self._list_frame,
                text=f"Load More ({remaining} remaining)",
                width=200, height=36,
                fg_color="#374151", hover_color="#4b5563",
                font=ctk.CTkFont(size=13),
                command=self._render_page,
            )
            self._load_more_btn.pack(pady=12)
        else:
            self._load_more_btn = None

    def _render_row(self, row_data: dict) -> None:
        is_inactive = row_data.get("is_inactive", False)
        row_bg = "#2d0d0d" if is_inactive else "#1e1e35"  # dark red tint for inactive
        row = ctk.CTkFrame(
            self._list_frame, fg_color=row_bg, corner_radius=6,
        )
        row.pack(fill="x", pady=2, padx=4)

        # Selection checkbox
        sid_ = row_data["id"]
        chk = ctk.CTkCheckBox(
            row, text="", width=24, checkbox_width=20, checkbox_height=20,
            command=lambda i=sid_: self._on_row_check(i),
        )
        if sid_ in self._selected_ids:
            chk.select()
        chk.pack(side="left", padx=(12, 0))
        self._row_checks[sid_] = chk

        # Name (+ INACTIVE badge if applicable)
        name_text = row_data["full_name"]
        name_color = "#ff6b6b" if is_inactive else "#e0e0e0"
        ctk.CTkLabel(
            row, text=name_text,
            font=ctk.CTkFont(size=13), text_color=name_color,
            width=190, anchor="w",
        ).pack(side="left", padx=(8, 4), pady=8)

        # RFID
        rfid_text  = row_data["card_id"] if row_data["card_id"] else "—"
        rfid_color = "#d0d0e0" if row_data["card_id"] else "#4b5563"
        ctk.CTkLabel(
            row, text=rfid_text,
            font=ctk.CTkFont(size=12), text_color=rfid_color,
            width=140, anchor="w",
        ).pack(side="left", padx=4)

        # Sections
        ctk.CTkLabel(
            row, text=row_data["sections"],
            font=ctk.CTkFont(size=12), text_color="#9ca3af",
            width=190, anchor="w",
        ).pack(side="left", padx=4)

        # Attendance %
        pct_text  = row_data.get("attendance_pct", "—")
        level = self._risk.get(row_data["id"])
        pct_color = {
            "green": "#4ade80",     # OK
            "yellow": "#facc15",    # at risk
            "red": "#f87171",       # candidate for removal
        }.get(level, "#6b7280")     # no data yet
        ctk.CTkLabel(
            row, text=pct_text,
            font=ctk.CTkFont(size=12, weight="bold"), text_color=pct_color,
            width=90, anchor="w",
        ).pack(side="left", padx=4)

        # Action buttons
        btn_frame = ctk.CTkFrame(row, fg_color="transparent", width=250)
        btn_frame.pack(side="right", padx=8)
        btn_frame.pack_propagate(False)

        ctk.CTkButton(
            btn_frame, text="Attendance", width=92, height=32,
            fg_color="#065f46", hover_color="#047857",
            font=ctk.CTkFont(size=12),
            command=lambda sid=row_data["id"], n=row_data["full_name"]:
                self._open_attendance_dialog(sid, n),
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            btn_frame, text="Edit", width=70, height=32,
            fg_color="#374151", hover_color="#4b5563",
            font=ctk.CTkFont(size=12),
            command=lambda sid=row_data["id"]: self._edit_student(sid),
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            btn_frame, text="Delete", width=70, height=32,
            fg_color="#7f1d1d", hover_color="#991b1b",
            font=ctk.CTkFont(size=12),
            command=lambda sid=row_data["id"], n=row_data["full_name"]:
                self._delete_student(sid, n),
        ).pack(side="left")

    # ──────────────────────────────────────────────────────────────────────────
    # Bulk selection / delete
    # ──────────────────────────────────────────────────────────────────────────

    def _update_delete_btn(self) -> None:
        self._delete_sel_btn.configure(
            text=f"Delete Selected ({len(self._selected_ids)})"
        )

    def _on_row_check(self, student_id: int) -> None:
        chk = self._row_checks.get(student_id)
        if chk is not None and chk.get():
            self._selected_ids.add(student_id)
        else:
            self._selected_ids.discard(student_id)
        self._update_delete_btn()

    def _toggle_select_all(self) -> None:
        if self._select_all_var.get():
            self._selected_ids.update(r["id"] for r in self._display_rows)
        else:
            self._selected_ids.difference_update(r["id"] for r in self._display_rows)
        for sid, chk in self._row_checks.items():
            if sid in self._selected_ids:
                chk.select()
            else:
                chk.deselect()
        self._update_delete_btn()

    def _delete_selected(self) -> None:
        ids = list(self._selected_ids)
        if not ids:
            messagebox.showinfo("Delete Selected", "No students selected.", parent=self._app)
            return
        if not messagebox.askyesno(
            "Delete Students",
            f"Delete {len(ids)} selected student(s)?\n\n"
            "All their attendance records will also be permanently deleted.\n"
            "This cannot be undone.",
            parent=self._app,
        ):
            return
        failed = 0
        for sid in ids:
            ok, _msg = student_ctrl.delete_student(sid)
            if ok:
                self._selected_ids.discard(sid)
            else:
                failed += 1
        log_info(f"StudentsTab: bulk deleted {len(ids) - failed}/{len(ids)} students")
        self._select_all_var.set(False)
        self._load()
        if failed:
            messagebox.showerror("Error", f"{failed} student(s) could not be deleted.", parent=self._app)

    # ──────────────────────────────────────────────────────────────────────────
    # Sort helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _sort_by(self, key: str) -> None:
        if self._sort_key == key:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_key = key
            self._sort_asc = True
        self._apply_filter()

    def _update_sort_indicators(self) -> None:
        for key, btn in self._col_buttons.items():
            label = next(
                (lbl for lbl, k, _ in _COLUMNS if k == key), key
            )
            if key == self._sort_key:
                arrow = " ▲" if self._sort_asc else " ▼"
                btn.configure(text=label + arrow, text_color="#e0e0e0")
            else:
                btn.configure(text=label, text_color="#a0aec0")

    # ──────────────────────────────────────────────────────────────────────────
    # CRUD actions
    # ──────────────────────────────────────────────────────────────────────────

    def _add_student(self) -> None:
        dlg = StudentEditDialog(self._app, student_id=None)
        self._app.wait_window(dlg)
        if dlg.saved:
            self._load()

    def _edit_student(self, student_id: int) -> None:
        dlg = StudentEditDialog(self._app, student_id=student_id)
        self._app.wait_window(dlg)
        if dlg.saved:
            self._load()

    def _open_attendance_dialog(self, student_id: int, full_name: str) -> None:
        dlg = ManualAttendanceDialog(self._app, student_id, full_name)
        self._app.wait_window(dlg)
        self._load()  # Recalculate attendance percentages after manual changes

    def _delete_student(self, student_id: int, full_name: str) -> None:
        if not messagebox.askyesno(
            "Delete Student",
            f"Delete student '{full_name}'?\n\n"
            "All their attendance records will also be permanently deleted.",
            parent=self._app,
        ):
            return

        ok, msg = student_ctrl.delete_student(student_id)
        if ok:
            log_info(f"StudentsTab: deleted student_id={student_id} '{full_name}'")
            self._load()
        else:
            messagebox.showerror("Error", msg, parent=self._app)

    # ──────────────────────────────────────────────────────────────────────────
    # Event callbacks
    # ──────────────────────────────────────────────────────────────────────────

    def _on_search_change(self, *_args: object) -> None:
        """Called whenever the search box text changes — debounced 200ms."""
        if self._search_debounce_id is not None:
            self.after_cancel(self._search_debounce_id)
        self._search_debounce_id = self.after(200, self._apply_filter)

    # ──────────────────────────────────────────────────────────────────────────
    # Public hook
    # ──────────────────────────────────────────────────────────────────────────

    def on_tab_selected(self) -> None:
        """Called by App when this tab becomes active — reload data."""
        self._load()

