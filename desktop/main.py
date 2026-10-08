"""«КонсалтПро» — десктопная панель управления консалтинговыми услугами."""
import os
from datetime import datetime

import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk

import db
import reports

ACCENT = "#2D6A4F"
ACCENT_DARK = "#1B4332"
BG = "#F4F6F5"
UNITS = ["Все", "проект", "час", "день", "месяц"]
SERVICE_STATUSES = ["Все", "Активна", "Неактивна"]
REQUEST_STATUSES = ["Все статусы", "Новая", "В работе", "Завершена", "Отменена"]

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")


def fmt_price(value):
    return f"{float(value):,.0f}".replace(",", " ") + " ₽"


def fmt_date(value):
    if hasattr(value, "strftime"):
        return value.strftime("%d.%m.%Y")
    return str(value)


def parse_date(text):
    text = text.strip()
    if not text:
        return None
    return datetime.strptime(text, "%d.%m.%Y").date()


def parse_number(text, integer=False):
    text = text.strip().replace("\u00a0", "").replace(" ", "")
    if not text:
        return None
    if integer:
        return int(text)
    return float(text)


class ServiceDialog(ctk.CTkToplevel):
    """Модальная форма добавления / редактирования услуги."""

    def __init__(self, master, categories, data=None, on_save=None):
        super().__init__(master)
        self.title("Услуга" if data is None else "Редактирование услуги")
        self.geometry("520x560")
        self.resizable(False, False)
        self.on_save = on_save
        self.data = data
        self.grab_set()

        pad = {"padx": 16, "pady": 6}
        ctk.CTkLabel(self, text="Категория", anchor="w").pack(fill="x", **pad)
        self.category = ctk.CTkComboBox(
            self, values=categories, state="readonly", height=34)
        self.category.set(categories[0])
        self.category.pack(fill="x", **pad)

        ctk.CTkLabel(self, text="Название", anchor="w").pack(fill="x", **pad)
        self.name = ctk.CTkEntry(self, height=34, placeholder_text="Например: Аудит бизнес-процессов")
        self.name.pack(fill="x", **pad)

        ctk.CTkLabel(self, text="Описание", anchor="w").pack(fill="x", **pad)
        self.description = ctk.CTkTextbox(self, height=96)
        self.description.pack(fill="x", **pad)

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", **pad)
        ctk.CTkLabel(row, text="Цена, ₽", anchor="w").grid(row=0, column=0, sticky="w")
        self.price = ctk.CTkEntry(row, width=150, height=34)
        self.price.grid(row=1, column=0, padx=(0, 8))
        ctk.CTkLabel(row, text="Единица измерения", anchor="w").grid(row=0, column=1, sticky="w")
        self.unit = ctk.CTkComboBox(
            row, values=["проект", "час", "день", "месяц"], state="readonly", width=150)
        self.unit.set("проект")
        self.unit.grid(row=1, column=1, padx=8)

        row2 = ctk.CTkFrame(self, fg_color="transparent")
        row2.pack(fill="x", **pad)
        ctk.CTkLabel(row2, text="Срок оказания, дней", anchor="w").grid(row=0, column=0, sticky="w")
        self.duration = ctk.CTkEntry(row2, width=150, height=34)
        self.duration.grid(row=1, column=0, padx=(0, 8))
        ctk.CTkLabel(row2, text="Статус", anchor="w").grid(row=0, column=1, sticky="w")
        self.status = ctk.CTkComboBox(
            row2, values=["Активна", "Неактивна"], state="readonly", width=150)
        self.status.set("Активна")
        self.status.grid(row=1, column=1, padx=8)

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.pack(fill="x", padx=16, pady=18)
        ctk.CTkButton(
            buttons, text="Сохранить", fg_color=ACCENT, hover_color=ACCENT_DARK,
            command=self.save).pack(side="left", expand=True, fill="x", padx=(0, 6))
        ctk.CTkButton(
            buttons, text="Отмена", fg_color="#6C757D", hover_color="#495057",
            command=self.destroy).pack(side="left", expand=True, fill="x", padx=6)

        if data:
            (_, category, name, description, price, unit, duration, active) = data
            self.category.set(category)
            self.name.insert(0, name)
            self.description.insert("1.0", description or "")
            self.price.insert(0, f"{float(price):.0f}")
            self.unit.set(unit)
            self.duration.insert(0, str(duration))
            self.status.set("Активна" if active else "Неактивна")

    def save(self):
        name = self.name.get().strip()
        if not name:
            messagebox.showwarning("Проверка", "Введите название услуги", parent=self)
            return
        try:
            price = parse_number(self.price.get())
            if price is None or price <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "Проверка", "Цена должна быть положительным числом", parent=self)
            return
        try:
            duration = parse_number(self.duration.get(), integer=True)
            if duration is None or duration < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "Проверка", "Срок должен быть целым числом (дней)", parent=self)
            return
        payload = (
            self.category.get(), name,
            self.description.get("1.0", "end").strip(),
            price, self.unit.get(), duration,
            1 if self.status.get() == "Активна" else 0,
        )
        if self.data is None:
            db.add_service(*payload)
        else:
            db.update_service(self.data[0], *payload)
        if self.on_save:
            self.on_save()
        self.destroy()


class RequestDialog(ctk.CTkToplevel):
    """Модальная форма добавления / редактирования заявки."""

    def __init__(self, master, service_choices, data=None, on_save=None):
        super().__init__(master)
        self.title("Заявка" if data is None else "Редактирование заявки")
        self.geometry("560x540")
        self.resizable(False, False)
        self.on_save = on_save
        self.data = data
        self.service_choices = service_choices
        self.grab_set()

        pad = {"padx": 16, "pady": 6}
        ctk.CTkLabel(self, text="Услуга", anchor="w").pack(fill="x", **pad)
        self.service = ctk.CTkComboBox(
            self, values=[c[1] for c in service_choices], state="readonly",
            height=34, width=480)
        if service_choices:
            self.service.set(service_choices[0][1])
        self.service.pack(fill="x", **pad)

        ctk.CTkLabel(self, text="Клиент", anchor="w").pack(fill="x", **pad)
        self.client = ctk.CTkEntry(self, height=34, placeholder_text="Организация или ФИО")
        self.client.pack(fill="x", **pad)

        ctk.CTkLabel(self, text="Контакт (телефон или e-mail)", anchor="w").pack(fill="x", **pad)
        self.contact = ctk.CTkEntry(self, height=34)
        self.contact.pack(fill="x", **pad)

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", **pad)
        ctk.CTkLabel(row, text="Дата заявки (ДД.ММ.ГГГГ)", anchor="w").grid(
            row=0, column=0, sticky="w")
        self.date = ctk.CTkEntry(row, width=170, height=34)
        self.date.grid(row=1, column=0, padx=(0, 8))
        ctk.CTkLabel(row, text="Статус", anchor="w").grid(row=0, column=1, sticky="w")
        self.status = ctk.CTkComboBox(
            row, values=REQUEST_STATUSES[1:], state="readonly", width=170)
        self.status.grid(row=1, column=1)

        ctk.CTkLabel(self, text="Комментарий", anchor="w").pack(fill="x", **pad)
        self.comment = ctk.CTkTextbox(self, height=80)
        self.comment.pack(fill="x", **pad)

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.pack(fill="x", padx=16, pady=16)
        ctk.CTkButton(
            buttons, text="Сохранить", fg_color=ACCENT, hover_color=ACCENT_DARK,
            command=self.save).pack(side="left", expand=True, fill="x", padx=(0, 6))
        ctk.CTkButton(
            buttons, text="Отмена", fg_color="#6C757D", hover_color="#495057",
            command=self.destroy).pack(side="left", expand=True, fill="x", padx=6)

        if data:
            (service_id, client, contact, date_value, status, comment) = data
            label = next(
                (lbl for sid, lbl in service_choices if sid == service_id), None)
            if label:
                self.service.set(label)
            self.client.insert(0, client or "")
            self.contact.insert(0, contact or "")
            self.date.insert(0, fmt_date(date_value))
            self.status.set(status)
            self.comment.insert("1.0", comment or "")
        else:
            self.date.insert(0, datetime.now().strftime("%d.%m.%Y"))
            self.status.set("Новая")

    def _service_id(self):
        label = self.service.get()
        code = label.split(" — ")[0]
        return int(code)

    def save(self):
        client = self.client.get().strip()
        if not client:
            messagebox.showwarning("Проверка", "Введите имя клиента", parent=self)
            return
        try:
            date_value = parse_date(self.date.get())
            if date_value is None:
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "Проверка", "Дата должна быть в формате ДД.ММ.ГГГГ", parent=self)
            return
        payload = (
            self._service_id(), client, self.contact.get().strip(), date_value,
            self.status.get(), self.comment.get("1.0", "end").strip(),
        )
        if self.data is None:
            db.add_request(*payload)
        else:
            db.update_request(self.data[0], *payload)
        if self.on_save:
            self.on_save()
        self.destroy()


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("КонсалтПро — панель консалтинговых услуг")
        self.geometry("1360x820")
        self.minsize(1100, 700)
        self.configure(fg_color=BG)

        self.categories = db.get_categories()
        self.units = UNITS
        self.svc_sort = ("id", False)
        self.req_sort = ("date", True)

        self._build_header()
        self._build_tabs()
        self._build_statusbar()
        self.refresh_all()

    # ---------- каркас ----------

    def _build_header(self):
        header = ctk.CTkFrame(self, height=64, fg_color=ACCENT, corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(
            header, text="  КонсалтПро",
            font=ctk.CTkFont(size=22, weight="bold"), text_color="white",
        ).pack(side="left", padx=(12, 8), pady=10)
        ctk.CTkLabel(
            header, text="управление консалтинговыми услугами",
            font=ctk.CTkFont(size=14), text_color="#D8F3DC",
        ).pack(side="left", pady=10)
        ctk.CTkButton(
            header, text="Обновить данные", width=150, height=32,
            fg_color=ACCENT_DARK, hover_color="#081C15",
            command=self.refresh_all,
        ).pack(side="right", padx=16, pady=16)

    def _build_tabs(self):
        self.tabview = ctk.CTkTabview(
            self, fg_color=BG, segmented_button_selected_color=ACCENT,
            segmented_button_selected_hover_color=ACCENT_DARK)
        self.tabview.pack(fill="both", expand=True, padx=12, pady=(8, 0))
        self.tabview.add("Услуги")
        self.tabview.add("Заявки")
        self.tabview.add("Отчёты")
        self._build_services_tab()
        self._build_requests_tab()
        self._build_reports_tab()

    def _build_statusbar(self):
        bar = ctk.CTkFrame(self, height=30, fg_color="#E9ECEF", corner_radius=0)
        bar.pack(fill="x", side="bottom")
        self.status_label = ctk.CTkLabel(bar, text="Подключение к базе данных…")
        self.status_label.pack(side="left", padx=12, pady=4)
        self.updated_label = ctk.CTkLabel(bar, text="")
        self.updated_label.pack(side="right", padx=12, pady=4)

    # ---------- таблицы ----------

    def _make_table(self, parent, columns, widths):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Treeview", background="white", foreground="#212529",
            fieldbackground="white", rowheight=30, font=("Segoe UI", 11))
        style.configure(
            "Treeview.Heading", background="#DEE2E6", foreground="#212529",
            font=("Segoe UI", 11, "bold"))
        style.map("Treeview.Heading",
                  background=[("active", "#CED4DA")])

        frame = ctk.CTkFrame(parent, fg_color="white", corner_radius=8)
        frame.pack(fill="both", expand=True)
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        for key, title, width in zip(columns, [c[1] for c in columns], widths):
            tree.heading(key, text=title,
                         command=lambda k=key: self._sort_tree(k, tree))
            tree.column(key, width=width, anchor="w")
        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        return tree

    def _sort_tree(self, key, tree):
        if tree is self.svc_tree:
            if self.svc_sort[0] == key:
                self.svc_sort = (key, not self.svc_sort[1])
            else:
                self.svc_sort = (key, False)
            self.load_services()
        elif tree is self.req_tree:
            if self.req_sort[0] == key:
                self.req_sort = (key, not self.req_sort[1])
            else:
                self.req_sort = (key, False)
            self.load_requests()

    # ---------- вкладка «Услуги» ----------

    def _build_services_tab(self):
        tab = self.tabview.tab("Услуги")
        paned = ctk.CTkFrame(tab, fg_color="transparent")
        paned.pack(fill="both", expand=True)

        left = ctk.CTkFrame(paned, width=270, fg_color="white", corner_radius=8)
        left.pack(side="left", fill="y", padx=(0, 10), pady=4)
        left.pack_propagate(False)
        ctk.CTkLabel(
            left, text="Фильтры",
            font=ctk.CTkFont(size=16, weight="bold")).pack(
            padx=14, pady=(14, 8), anchor="w")

        ctk.CTkLabel(left, text="Название (поиск)", anchor="w").pack(
            padx=14, pady=(6, 2), fill="x")
        self.svc_search = ctk.CTkEntry(left, height=32, placeholder_text="часть названия")
        self.svc_search.pack(padx=14, fill="x")
        self.svc_search.bind("<Return>", lambda e: self.load_services())

        ctk.CTkLabel(left, text="Категория", anchor="w").pack(
            padx=14, pady=(10, 2), fill="x")
        self.svc_category = ctk.CTkComboBox(
            left, values=["Все категории"] + self.categories,
            state="readonly", height=32, command=lambda _: self.load_services())
        self.svc_category.set("Все категории")
        self.svc_category.pack(padx=14, fill="x")

        ctk.CTkLabel(left, text="Единица измерения", anchor="w").pack(
            padx=14, pady=(10, 2), fill="x")
        self.svc_unit = ctk.CTkComboBox(
            left, values=self.units, state="readonly", height=32,
            command=lambda _: self.load_services())
        self.svc_unit.set("Все")
        self.svc_unit.pack(padx=14, fill="x")

        ctk.CTkLabel(left, text="Статус", anchor="w").pack(
            padx=14, pady=(10, 2), fill="x")
        self.svc_status = ctk.CTkComboBox(
            left, values=SERVICE_STATUSES, state="readonly", height=32,
            command=lambda _: self.load_services())
        self.svc_status.set("Все")
        self.svc_status.pack(padx=14, fill="x")

        price_row = ctk.CTkFrame(left, fg_color="transparent")
        price_row.pack(padx=14, pady=(10, 0), fill="x")
        ctk.CTkLabel(price_row, text="Цена, ₽", anchor="w").pack(fill="x")
        self.svc_price_min = ctk.CTkEntry(price_row, height=32, placeholder_text="от")
        self.svc_price_min.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.svc_price_max = ctk.CTkEntry(price_row, height=32, placeholder_text="до")
        self.svc_price_max.pack(side="left", fill="x", expand=True, padx=(4, 0))

        dur_row = ctk.CTkFrame(left, fg_color="transparent")
        dur_row.pack(padx=14, pady=(10, 0), fill="x")
        ctk.CTkLabel(dur_row, text="Срок оказания, дней", anchor="w").pack(fill="x")
        self.svc_dur_min = ctk.CTkEntry(dur_row, height=32, placeholder_text="от")
        self.svc_dur_min.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.svc_dur_max = ctk.CTkEntry(dur_row, height=32, placeholder_text="до")
        self.svc_dur_max.pack(side="left", fill="x", expand=True, padx=(4, 0))

        btn_row = ctk.CTkFrame(left, fg_color="transparent")
        btn_row.pack(padx=14, pady=14, fill="x")
        ctk.CTkButton(
            btn_row, text="Применить", fg_color=ACCENT, hover_color=ACCENT_DARK,
            height=32, command=self.load_services).pack(fill="x", pady=(0, 6))
        ctk.CTkButton(
            btn_row, text="Сбросить", fg_color="#6C757D", hover_color="#495057",
            height=32, command=self._reset_service_filters).pack(fill="x")

        right = ctk.CTkFrame(paned, fg_color="transparent")
        right.pack(side="left", fill="both", expand=True)

        toolbar = ctk.CTkFrame(right, fg_color="transparent")
        toolbar.pack(fill="x", pady=(4, 6))
        for text, cmd, color in (
            ("Добавить", self.add_service, ACCENT),
            ("Изменить", self.edit_service, "#096B72"),
            ("Удалить", self.delete_service, "#C0392B"),
        ):
            ctk.CTkButton(
                toolbar, text=text, width=110, height=32, fg_color=color,
                hover_color=ACCENT_DARK if color == ACCENT else color,
                command=cmd).pack(side="left", padx=(0, 8))
        self.svc_counter = ctk.CTkLabel(toolbar, text="", text_color="#495057")
        self.svc_counter.pack(side="right", padx=6)

        self.svc_tree = self._make_table(
            right,
            [("id", "ID", 60), ("category", "Категория", 190),
             ("name", "Название", 330), ("price", "Цена", 120),
             ("unit", "Ед. изм.", 100), ("duration", "Срок, дней", 110),
             ("status", "Статус", 110)],
            [60, 190, 330, 120, 100, 110, 110])
        self.svc_tree.bind("<Double-1>", lambda e: self.edit_service())

    def _reset_service_filters(self):
        self.svc_search.delete(0, "end")
        self.svc_category.set("Все категории")
        self.svc_unit.set("Все")
        self.svc_status.set("Все")
        for entry in (self.svc_price_min, self.svc_price_max,
                      self.svc_dur_min, self.svc_dur_max):
            entry.delete(0, "end")
        self.load_services()

    def _service_filter_values(self):
        try:
            price_min = parse_number(self.svc_price_min.get())
            price_max = parse_number(self.svc_price_max.get())
        except ValueError:
            messagebox.showwarning("Проверка", "Цена: введите число")
            return None
        try:
            dur_min = parse_number(self.svc_dur_min.get(), integer=True)
            dur_max = parse_number(self.svc_dur_max.get(), integer=True)
        except ValueError:
            messagebox.showwarning("Проверка", "Срок: введите целое число")
            return None
        return dict(
            search=self.svc_search.get().strip(),
            category=self.svc_category.get(),
            unit=self.svc_unit.get(),
            status=self.svc_status.get(),
            price_min=price_min, price_max=price_max,
            duration_min=dur_min, duration_max=dur_max,
        )

    def load_services(self):
        values = self._service_filter_values()
        if values is None:
            return
        rows = db.list_services(
            sort=self.svc_sort[0], desc=self.svc_sort[1], **values)
        self.svc_tree.delete(*self.svc_tree.get_children())
        for row in rows:
            (sid, category, name, price, unit, duration, active) = row
            self.svc_tree.insert("", "end", iid=str(sid), values=(
                sid, category, name, fmt_price(price), unit,
                duration, "Активна" if active else "Неактивна"))
        self.svc_counter.configure(
            text=f"Показано {len(rows)} из {db.count_services()}")
        self._touch_status()

    def add_service(self):
        ServiceDialog(self, self.categories, on_save=self.load_services)

    def edit_service(self):
        selected = self.svc_tree.selection()
        if not selected:
            messagebox.showinfo("Услуги", "Выберите строку в таблице")
            return
        data = db.get_service(int(selected[0]))
        if data:
            ServiceDialog(self, self.categories, data=data,
                          on_save=self.load_services)

    def delete_service(self):
        selected = self.svc_tree.selection()
        if not selected:
            messagebox.showinfo("Услуги", "Выберите строку в таблице")
            return
        if messagebox.askyesno(
                "Удаление",
                "Удалить услугу вместе со связанными заявками?"):
            db.delete_service(int(selected[0]))
            self.load_services()
            self.load_requests()

    # ---------- вкладка «Заявки» ----------

    def _build_requests_tab(self):
        tab = self.tabview.tab("Заявки")
        paned = ctk.CTkFrame(tab, fg_color="transparent")
        paned.pack(fill="both", expand=True)

        left = ctk.CTkFrame(paned, width=270, fg_color="white", corner_radius=8)
        left.pack(side="left", fill="y", padx=(0, 10), pady=4)
        left.pack_propagate(False)
        ctk.CTkLabel(
            left, text="Фильтры",
            font=ctk.CTkFont(size=16, weight="bold")).pack(
            padx=14, pady=(14, 8), anchor="w")

        ctk.CTkLabel(left, text="Статус", anchor="w").pack(
            padx=14, pady=(6, 2), fill="x")
        self.req_status = ctk.CTkComboBox(
            left, values=REQUEST_STATUSES, state="readonly", height=32,
            command=lambda _: self.load_requests())
        self.req_status.set("Все статусы")
        self.req_status.pack(padx=14, fill="x")

        ctk.CTkLabel(left, text="Период с", anchor="w").pack(
            padx=14, pady=(10, 2), fill="x")
        self.req_date_from = ctk.CTkEntry(
            left, height=32, placeholder_text="ДД.ММ.ГГГГ")
        self.req_date_from.pack(padx=14, fill="x")

        ctk.CTkLabel(left, text="Период по", anchor="w").pack(
            padx=14, pady=(10, 2), fill="x")
        self.req_date_to = ctk.CTkEntry(
            left, height=32, placeholder_text="ДД.ММ.ГГГГ")
        self.req_date_to.pack(padx=14, fill="x")

        ctk.CTkLabel(left, text="Клиент или услуга", anchor="w").pack(
            padx=14, pady=(10, 2), fill="x")
        self.req_search = ctk.CTkEntry(left, height=32, placeholder_text="поиск")
        self.req_search.pack(padx=14, fill="x")
        self.req_search.bind("<Return>", lambda e: self.load_requests())

        btn_row = ctk.CTkFrame(left, fg_color="transparent")
        btn_row.pack(padx=14, pady=14, fill="x")
        ctk.CTkButton(
            btn_row, text="Применить", fg_color=ACCENT, hover_color=ACCENT_DARK,
            height=32, command=self.load_requests).pack(fill="x", pady=(0, 6))
        ctk.CTkButton(
            btn_row, text="Сбросить", fg_color="#6C757D", hover_color="#495057",
            height=32, command=self._reset_request_filters).pack(fill="x")

        right = ctk.CTkFrame(paned, fg_color="transparent")
        right.pack(side="left", fill="both", expand=True)

        toolbar = ctk.CTkFrame(right, fg_color="transparent")
        toolbar.pack(fill="x", pady=(4, 6))
        for text, cmd, color in (
            ("Создать", self.add_request, ACCENT),
            ("Изменить", self.edit_request, "#096B72"),
            ("Удалить", self.delete_request, "#C0392B"),
        ):
            ctk.CTkButton(
                toolbar, text=text, width=110, height=32, fg_color=color,
                hover_color=ACCENT_DARK if color == ACCENT else color,
                command=cmd).pack(side="left", padx=(0, 8))
        self.req_counter = ctk.CTkLabel(toolbar, text="", text_color="#495057")
        self.req_counter.pack(side="right", padx=6)

        self.req_tree = self._make_table(
            right,
            [("id", "ID", 55), ("service", "Услуга", 300),
             ("client", "Клиент", 180), ("contact", "Контакт", 170),
             ("date", "Дата", 100), ("status", "Статус", 110),
             ("comment", "Комментарий", 260)],
            [55, 300, 180, 170, 100, 110, 260])
        self.req_tree.bind("<Double-1>", lambda e: self.edit_request())

    def _reset_request_filters(self):
        self.req_status.set("Все статусы")
        self.req_date_from.delete(0, "end")
        self.req_date_to.delete(0, "end")
        self.req_search.delete(0, "end")
        self.load_requests()

    def _request_filter_values(self):
        try:
            date_from = parse_date(self.req_date_from.get())
            date_to = parse_date(self.req_date_to.get())
        except ValueError:
            messagebox.showwarning(
                "Проверка", "Дата: формат ДД.ММ.ГГГГ")
            return None
        return dict(
            status=self.req_status.get(),
            date_from=date_from, date_to=date_to,
            search=self.req_search.get().strip(),
        )

    def load_requests(self):
        values = self._request_filter_values()
        if values is None:
            return
        values["sort"] = self.req_sort[0]
        values["desc"] = self.req_sort[1]
        rows = db.list_requests(**values)
        self.req_tree.delete(*self.req_tree.get_children())
        for row in rows:
            (rid, service, client, contact, date_value, status,
             comment, _service_id) = row
            self.req_tree.insert("", "end", iid=str(rid), values=(
                rid, service, client, contact, fmt_date(date_value),
                status, comment or ""))
        self.req_counter.configure(
            text=f"Показано {len(rows)} из {db.count_requests()}")
        self._touch_status()

    def add_request(self):
        RequestDialog(self, db.get_service_choices(), on_save=self.load_requests)

    def edit_request(self):
        selected = self.req_tree.selection()
        if not selected:
            messagebox.showinfo("Заявки", "Выберите строку в таблице")
            return
        data = db.get_request(int(selected[0]))
        if data:
            RequestDialog(self, db.get_service_choices(), data=data,
                          on_save=self.load_requests)

    def delete_request(self):
        selected = self.req_tree.selection()
        if not selected:
            messagebox.showinfo("Заявки", "Выберите строку в таблице")
            return
        if messagebox.askyesno("Удаление", "Удалить выбранную заявку?"):
            db.delete_request(int(selected[0]))
            self.load_requests()

    # ---------- вкладка «Отчёты» ----------

    def _build_reports_tab(self):
        tab = self.tabview.tab("Отчёты")

        stats = db.summary_stats()
        summary = ctk.CTkFrame(tab, fg_color="white", corner_radius=8)
        summary.pack(fill="x", pady=(4, 10))
        cards = [
            ("Услуг всего", str(stats["services"][0])),
            ("Активных", str(stats["services"][1] or 0)),
            ("Неактивных", str(stats["services"][2] or 0)),
            ("Заявок всего", str(stats["requests"][0])),
            ("Новых", str(stats["requests"][1] or 0)),
            ("В работе", str(stats["requests"][2] or 0)),
            ("Завершено", str(stats["requests"][3] or 0)),
            ("Отменено", str(stats["requests"][4] or 0)),
        ]
        for title, value in cards:
            card = ctk.CTkFrame(summary, fg_color="#EDF6F0", corner_radius=8)
            card.pack(side="left", expand=True, fill="both", padx=6, pady=10)
            ctk.CTkLabel(
                card, text=value,
                font=ctk.CTkFont(size=24, weight="bold"),
                text_color=ACCENT_DARK).pack(pady=(10, 0))
            ctk.CTkLabel(card, text=title, text_color="#495057").pack(
                pady=(0, 10))

        def card_create(title, description, with_dates, command):
            frame = ctk.CTkFrame(tab, fg_color="white", corner_radius=8)
            frame.pack(fill="x", pady=5)
            body = ctk.CTkFrame(frame, fg_color="transparent")
            body.pack(fill="x", padx=16, pady=12)
            text = ctk.CTkFrame(body, fg_color="transparent")
            text.pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(
                text, text=title,
                font=ctk.CTkFont(size=15, weight="bold"),
                anchor="w").pack(fill="x")
            ctk.CTkLabel(
                text, text=description, text_color="#6C757D",
                anchor="w", justify="left").pack(fill="x")
            controls = ctk.CTkFrame(body, fg_color="transparent")
            controls.pack(side="right")
            entries = []
            if with_dates:
                for label, default in (
                        ("с", "01.08.2026"), ("по", "08.10.2026")):
                    box = ctk.CTkFrame(controls, fg_color="transparent")
                    box.pack(side="left", padx=4)
                    ctk.CTkLabel(box, text=label).pack()
                    entry = ctk.CTkEntry(box, width=110, height=30)
                    entry.insert(0, default)
                    entry.pack()
                    entries.append(entry)
            fmt = ctk.CTkSegmentedButton(
                controls, values=["Excel", "TXT"],
                selected_color=ACCENT, selected_hover_color=ACCENT_DARK)
            fmt.set("Excel")
            fmt.pack(side="left", padx=10, pady=(14, 0))
            ctk.CTkButton(
                controls, text="Сформировать", width=140, height=32,
                fg_color=ACCENT, hover_color=ACCENT_DARK,
                command=lambda: command(entries, fmt)).pack(
                side="left", padx=(10, 0), pady=(14, 0))
            return frame

        card_create(
            "Услуги по категориям",
            "Количество, минимальная, максимальная и средняя цена\nпо каждому направлению консалтинга",
            False, self.report_services)
        card_create(
            "Заявки за период",
            "Список заявок клиентов за выбранный период:\nуслуга, клиент, дата, статус",
            True, self.report_requests)
        card_create(
            "Доход по категориям",
            "Завершённые заявки и сумма по направлениям\nза выбранный период",
            True, self.report_revenue)

    def _save_path(self, fmt, initial):
        ext = ".xlsx" if fmt == "Excel" else ".txt"
        filetypes = (
            [("Книга Excel", "*.xlsx")] if fmt == "Excel"
            else [("Текстовый файл", "*.txt")])
        path = filedialog.asksaveasfilename(
            initialfile=initial + ext, defaultextension=ext, filetypes=filetypes)
        return path or None

    def report_services(self, entries, fmt):
        rows = db.report_services_by_category()
        caption = "Отчёт по услугам в разрезе категорий"
        headers = ["Категория", "Услуг, шт", "Мин. цена, ₽",
                   "Макс. цена, ₽", "Средняя цена, ₽"]
        data = [(r[0], r[1], fmt_price(r[2]), fmt_price(r[3]), fmt_price(r[4]))
                for r in rows]
        path = self._save_path(fmt.get(), "Услуги_по_категориям")
        if not path:
            return
        self._write_report(path, fmt.get(), caption, headers, data)

    def report_requests(self, entries, fmt):
        try:
            date_from = parse_date(entries[0].get())
            date_to = parse_date(entries[1].get())
            if date_from is None or date_to is None:
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "Проверка", "Укажите даты в формате ДД.ММ.ГГГГ")
            return
        rows = db.report_requests_period(date_from, date_to)
        caption = (f"Отчёт по заявкам за период "
                   f"{date_from.strftime('%d.%m.%Y')} — {date_to.strftime('%d.%m.%Y')}")
        headers = ["№", "Услуга", "Клиент", "Дата", "Статус"]
        data = [(r[0], r[1], r[2], fmt_date(r[3]), r[4]) for r in rows]
        path = self._save_path(fmt.get(), "Заявки_за_период")
        if not path:
            return
        self._write_report(path, fmt.get(), caption, headers, data)

    def report_revenue(self, entries, fmt):
        try:
            date_from = parse_date(entries[0].get())
            date_to = parse_date(entries[1].get())
            if date_from is None or date_to is None:
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "Проверка", "Укажите даты в формате ДД.ММ.ГГГГ")
            return
        rows = db.report_revenue_by_category(date_from, date_to)
        caption = (f"Расчёт дохода по категориям за период "
                   f"{date_from.strftime('%d.%m.%Y')} — {date_to.strftime('%d.%m.%Y')}")
        headers = ["Категория", "Завершённых заявок", "Сумма, ₽"]
        data = [(r[0], r[1], fmt_price(r[2])) for r in rows]
        path = self._save_path(fmt.get(), "Доход_по_категориям")
        if not path:
            return
        self._write_report(path, fmt.get(), caption, headers, data)

    def _write_report(self, path, fmt, caption, headers, data):
        try:
            if fmt == "Excel":
                reports.write_excel(path, caption, headers, data)
            else:
                reports.write_txt(path, caption, headers, data)
        except Exception as exc:
            messagebox.showerror("Ошибка", f"Не удалось сохранить отчёт:\n{exc}")
            return
        messagebox.showinfo("Отчёт", f"Отчёт сохранён:\n{path}")
        self._touch_status()

    # ---------- служебное ----------

    def refresh_all(self):
        self.categories = db.get_categories()
        ok = db.ping()
        try:
            self.load_services()
            self.load_requests()
        except Exception as exc:
            messagebox.showerror(
                "База данных",
                f"Не удалось загрузить данные:\n{exc}")
            ok = False
        self.status_label.configure(
            text="База данных: подключено" if ok
            else "База данных: нет подключения")
        self._touch_status()

    def _touch_status(self):
        self.updated_label.configure(
            text="Обновлено: " + datetime.now().strftime("%H:%M:%S"))


if __name__ == "__main__":
    app = App()
    app.mainloop()
