"""КонсалтПро — мобильное приложение (Flet).

Разделы: каталог услуг с фильтрами, заявки, статистика.
Синхронизация с десктоп-приложением выполняется через общую облачную
базу данных MySQL: заявка, созданная на телефоне, сразу появляется
на ПК, и наоборот.

Запуск на компьютере:  python main.py
Скриншоты для отчёта:  CONSALT_SHOTS=1 python main.py
"""
import asyncio
import os
from datetime import datetime

import flet as ft

import db

GREEN = ft.Colors.GREEN_800
GREEN_SOFT = ft.Colors.GREEN_100
WHITE = ft.Colors.WHITE
GREY = ft.Colors.GREY_700
REQUEST_STATUSES = ["Новая", "В работе", "Завершена", "Отменена"]
STATUS_COLORS = {
    "Новая": ft.Colors.BLUE,
    "В работе": ft.Colors.ORANGE,
    "Завершена": ft.Colors.GREEN_700,
    "Отменена": ft.Colors.RED_700,
}


def fmt_price(value):
    if value is None:
        return "—"
    return f"{int(value):,}".replace(",", " ")


def fmt_date(value):
    if isinstance(value, datetime):
        return value.strftime("%d.%m.%Y")
    if hasattr(value, "strftime"):
        return value.strftime("%d.%m.%Y")
    return str(value)


def parse_date(text):
    try:
        return datetime.strptime(text.strip(), "%d.%m.%Y").date()
    except ValueError:
        return None


class MobileApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.online = True
        self.svc_rows = []
        self.req_rows = []
        self.stat_rows = []
        self.svc_search_task = None
        self.req_search_task = None

        page.title = "КонсалтПро"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.bgcolor = ft.Colors.GREY_100
        page.padding = 0
        page.enable_screenshots = True
        page.window.width = 400
        page.window.height = 850
        page.window.min_width = 340
        page.window.min_height = 600
        page.window.center = True

        self._build_header()
        self._build_catalog()
        self._build_requests()
        self._build_stats()

        self.body = ft.Container(expand=True, content=self.tab_catalog)
        self.nav = ft.NavigationBar(
            selected_index=0,
            bgcolor=ft.Colors.WHITE,
            on_change=self._on_nav,
            destinations=[
                ft.NavigationBarDestination(
                    icon=ft.Icons.MENU_BOOK_OUTLINED,
                    selected_icon=ft.Icons.MENU_BOOK,
                    label="Каталог"),
                ft.NavigationBarDestination(
                    icon=ft.Icons.LIST_ALT_OUTLINED,
                    selected_icon=ft.Icons.LIST_ALT,
                    label="Заявки"),
                ft.NavigationBarDestination(
                    icon=ft.Icons.INSIGHTS_OUTLINED,
                    selected_icon=ft.Icons.INSIGHTS,
                    label="Статистика"),
            ],
        )
        page.add(
            ft.Column(
                [
                    self.header,
                    self.progress,
                    ft.Container(self.body, expand=True),
                    self.nav,
                ],
                expand=True,
                spacing=0,
            )
        )
        page.run_task(self._startup)

    # ---------- каркас ----------

    def _build_header(self):
        self.conn_text = ft.Text("подключение…", size=11,
                                 color=ft.Colors.WHITE70)
        self.header = ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text("КонсалтПро", size=20,
                                    weight=ft.FontWeight.BOLD, color=WHITE),
                            ft.Text("каталог услуг и заявки", size=12,
                                    color=ft.Colors.WHITE70),
                        ],
                        spacing=0,
                        expand=True,
                    ),
                    ft.Column(
                        [
                            ft.IconButton(
                                ft.Icons.REFRESH_ROUNDED, icon_color=WHITE,
                                tooltip="Обновить данные",
                                on_click=self._on_refresh),
                            self.conn_text,
                        ],
                        spacing=0,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=GREEN,
            padding=ft.Padding.symmetric(horizontal=16, vertical=14),
        )
        self.progress = ft.ProgressBar(
            value=None, visible=False, color=GREEN,
            bar_height=3, bgcolor=ft.Colors.TRANSPARENT)

    def _filter_card(self, *controls):
        return ft.Card(
            content=ft.Container(
                ft.Column(controls, spacing=10),
                padding=ft.Padding.symmetric(horizontal=16, vertical=14),
            ),
            elevation=1,
            margin=ft.Margin.symmetric(horizontal=10, vertical=4),
        )

    def _count_row(self, label_control):
        return ft.Row(
            [label_control],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

    # ---------- каталог ----------

    def _build_catalog(self):
        self.svc_search = ft.TextField(
            hint_text="Поиск по названию…",
            prefix_icon=ft.Icons.SEARCH,
            dense=True, text_size=14,
            content_padding=ft.Padding.symmetric(horizontal=12, vertical=8),
            on_change=self._on_svc_search,
        )
        self.svc_category = ft.Dropdown(
            label="Категория",
            options=[ft.DropdownOption(key="", text="Все категории")],
            value="", dense=True, text_size=14,
            on_select=self._on_filter,
        )
        self.svc_status = ft.Dropdown(
            label="Статус",
            options=[
                ft.DropdownOption(key="", text="Все"),
                ft.DropdownOption(key="Активна", text="Активна"),
                ft.DropdownOption(key="Неактивна", text="Неактивна"),
            ],
            value="", dense=True, text_size=14,
            on_select=self._on_filter,
        )
        self.svc_count = ft.Text("загрузка…", size=12, color=GREY)
        self.svc_list = ft.ListView(
            expand=True, spacing=6,
            padding=ft.Padding.symmetric(horizontal=0, vertical=8),
        )
        empty = ft.Text("", size=12)
        self.svc_empty = empty
        self.tab_catalog = ft.Column(
            [
                self._filter_card(
                    self.svc_search,
                    ft.Row([self.svc_category, self.svc_status],
                           spacing=10, expand=True),
                ),
                ft.Container(
                    self._count_row(self.svc_count),
                    padding=ft.Padding.symmetric(horizontal=18, vertical=4),
                ),
                self.svc_list,
            ],
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )

    def _service_card(self, row):
        sid, cat, name, price, unit, duration, active = row
        status_text = "Активна" if active else "Неактивна"
        status_color = (ft.Colors.GREEN_700 if active
                        else ft.Colors.GREY_500)
        return ft.Card(
            content=ft.Container(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.WORK_OUTLINE, color=GREEN),
                    title=ft.Text(name, size=14,
                                  weight=ft.FontWeight.W_600,
                                  max_lines=1,
                                  overflow=ft.TextOverflow.ELLIPSIS),
                    subtitle=ft.Text(
                        f"{cat} • {fmt_price(price)} ₽ / {unit} • "
                        f"{duration} дн.",
                        size=12, color=GREY,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    trailing=ft.Column(
                        [
                            ft.Icon(ft.Icons.CHEVRON_RIGHT, color=GREY,
                                    size=18),
                            ft.Text(status_text, size=10,
                                    color=status_color),
                        ],
                        spacing=0,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    on_click=self._on_service_click,
                    data=row,
                    content_padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                ),
                padding=ft.Padding.symmetric(horizontal=4, vertical=2),
            ),
            elevation=1,
            margin=ft.Margin.symmetric(horizontal=10),
        )

    # ---------- заявки ----------

    def _build_requests(self):
        self.req_status = ft.Dropdown(
            label="Статус",
            options=[ft.DropdownOption(key="", text="Все статусы")]
            + [ft.DropdownOption(key=s, text=s) for s in REQUEST_STATUSES],
            value="", dense=True, text_size=14,
            on_select=self._on_filter,
        )
        self.req_search = ft.TextField(
            hint_text="Клиент или услуга…",
            prefix_icon=ft.Icons.SEARCH,
            dense=True, text_size=14,
            content_padding=ft.Padding.symmetric(horizontal=12, vertical=8),
            on_change=self._on_req_search,
        )
        self.req_count = ft.Text("загрузка…", size=12, color=GREY)
        self.req_list = ft.ListView(
            expand=True, spacing=6,
            padding=ft.Padding.symmetric(horizontal=0, vertical=8),
        )
        self.tab_requests = ft.Column(
            [
                self._filter_card(self.req_search, self.req_status),
                ft.Container(
                    self._count_row(self.req_count),
                    padding=ft.Padding.symmetric(horizontal=18, vertical=4),
                ),
                self.req_list,
            ],
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )

    def _request_card(self, row):
        rid, service, client, contact, req_date, status, comment, _sid = row
        color = STATUS_COLORS.get(status, GREY)
        return ft.Card(
            content=ft.Container(
                ft.ListTile(
                    leading=ft.Container(
                        ft.Icon(ft.Icons.CIRCLE, size=14, color=color),
                        padding=ft.Padding.only(top=4),
                    ),
                    title=ft.Text(client, size=14,
                                  weight=ft.FontWeight.W_600,
                                  max_lines=1,
                                  overflow=ft.TextOverflow.ELLIPSIS),
                    subtitle=ft.Text(
                        f"{service} • {fmt_date(req_date)}",
                        size=12, color=GREY,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    trailing=ft.Container(
                        ft.Text(status, size=11, color=WHITE,
                                weight=ft.FontWeight.W_600),
                        bgcolor=color,
                        padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                        border_radius=10,
                    ),
                    on_click=self._on_request_click,
                    data=row,
                    content_padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                ),
                padding=ft.Padding.symmetric(horizontal=4, vertical=2),
            ),
            elevation=1,
            margin=ft.Margin.symmetric(horizontal=10),
        )

    # ---------- статистика ----------

    def _build_stats(self):
        self.stats_grid = ft.ResponsiveRow(
            [], spacing=10, run_spacing=10,
        )
        self.stats_categories = ft.Column(spacing=6)
        self.stats_sync = ft.Text("", size=12, color=GREY)
        self.tab_stats = ft.ListView(
            [
                ft.Container(self.stats_grid,
                             padding=ft.Padding.symmetric(horizontal=14, vertical=10)),
                ft.Container(
                    ft.Column(
                        [
                            ft.Text("Услуги по категориям", size=15,
                                    weight=ft.FontWeight.BOLD),
                            self.stats_categories,
                        ],
                        spacing=8,
                    ),
                    padding=ft.Padding.symmetric(horizontal=16, vertical=6),
                ),
                ft.Container(
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.FilledButton(
                                        "Обновить статистику",
                                        icon=ft.Icons.REFRESH_ROUNDED,
                                        on_click=self._on_refresh),
                                ],
                            ),
                            self.stats_sync,
                        ],
                        spacing=8,
                    ),
                    padding=ft.Padding.symmetric(horizontal=16, vertical=10),
                ),
            ],
            expand=True,
            padding=ft.Padding.only(bottom=12),
        )

    def _stat_box(self, value, label, color):
        return ft.Container(
            ft.Column(
                [
                    ft.Text(str(value), size=24,
                            weight=ft.FontWeight.BOLD, color=color),
                    ft.Text(label, size=12, color=GREY),
                ],
                spacing=0,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            padding=ft.Padding.symmetric(horizontal=8, vertical=14),
            col=6,
        )

    # ---------- навигация ----------

    def _on_nav(self, e):
        self.set_tab(e.control.selected_index)

    def set_tab(self, index):
        contents = [self.tab_catalog, self.tab_requests, self.tab_stats]
        self.body.content = contents[index]
        self.page.update()

    # ---------- события ----------

    async def _on_refresh(self, e=None):
        await self.reload_all()

    async def _on_svc_search(self, e):
        if self.svc_search_task:
            self.svc_search_task.cancel()
        self.svc_search_task = asyncio.ensure_future(self._debounced_catalog())

    async def _debounced_catalog(self):
        await asyncio.sleep(0.4)
        await self.reload_catalog()

    async def _on_req_search(self, e):
        if self.req_search_task:
            self.req_search_task.cancel()
        self.req_search_task = asyncio.ensure_future(self._debounced_requests())

    async def _debounced_requests(self):
        await asyncio.sleep(0.4)
        await self.reload_requests()

    async def _on_filter(self, e):
        if e.control is self.svc_category or e.control is self.svc_status:
            await self.reload_catalog()
        else:
            await self.reload_requests()

    async def _on_service_click(self, e):
        row = e.control.data
        self.progress.visible = True
        self.page.update()
        try:
            detail = await asyncio.to_thread(db.get_service, row[0])
        finally:
            self.progress.visible = False
        if detail is None:
            return
        _cat_id, cat, name, description, price, unit, duration, active = detail
        status_text = "Активна" if active else "Неактивна"
        lines = [
            ("Категория", cat),
            ("Цена", f"{fmt_price(price)} ₽ / {unit}"),
            ("Срок оказания", f"{duration} дн."),
            ("Статус", status_text),
            ("Описание", description or "—"),
        ]
        content = ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(label, size=13, color=GREY, width=130),
                        ft.Text(value, size=13, expand=True),
                    ]
                )
                for label, value in lines
            ],
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
        )
        dialog = ft.AlertDialog(
            title=ft.Text(name, size=16, weight=ft.FontWeight.BOLD),
            content=ft.Container(content, width=340),
            actions=[
                ft.TextButton("Закрыть",
                              on_click=lambda _: self.page.pop_dialog()),
                ft.FilledButton(
                    "Оставить заявку",
                    bgcolor=GREEN,
                    on_click=lambda _: self._open_request_form(row[0]),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.show_dialog(dialog)

    def _open_request_form(self, service_id):
        self.service_id_input = service_id
        self.client_name = ft.TextField(
            label="Ваше имя *", dense=True, text_size=14)
        self.client_contact = ft.TextField(
            label="Телефон или e-mail", dense=True, text_size=14)
        self.request_date = ft.TextField(
            label="Дата заявки", dense=True, text_size=14,
            value=datetime.now().strftime("%d.%m.%Y"),
            hint_text="ДД.ММ.ГГГГ")
        self.request_comment = ft.TextField(
            label="Комментарий", multiline=True, min_lines=2, max_lines=3,
            dense=True, text_size=14)
        self.form_error = ft.Text("", size=12, color=ft.Colors.RED_700)
        dialog = ft.AlertDialog(
            title=ft.Text("Новая заявка", size=16,
                          weight=ft.FontWeight.BOLD),
            content=ft.Container(
                ft.Column(
                    [
                        self.client_name,
                        self.client_contact,
                        self.request_date,
                        self.request_comment,
                        self.form_error,
                    ],
                    spacing=8,
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=340,
            ),
            actions=[
                ft.TextButton("Отмена",
                              on_click=lambda _: self.page.pop_dialog()),
                ft.FilledButton("Отправить", bgcolor=GREEN,
                                on_click=self._submit_request),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.show_dialog(dialog)

    async def _submit_request(self, e):
        name = self.client_name.value.strip()
        if not name:
            self.form_error.value = "Укажите имя — это обязательное поле"
            self.page.update()
            return
        request_date = parse_date(self.request_date.value) \
            or datetime.now().date()
        try:
            new_id = await asyncio.to_thread(
                db.add_request,
                self.service_id_input,
                name,
                self.client_contact.value.strip(),
                request_date,
                "Новая",
                self.request_comment.value.strip(),
            )
        except Exception:
            self.form_error.value = "Ошибка отправки: нет связи с базой"
            self.page.update()
            return
        self.page.pop_dialog()
        self._snack(f"Заявка №{new_id} отправлена")
        await self.reload_requests()
        await self.reload_stats()

    async def _on_request_click(self, e):
        row = e.control.data
        rid, service, client, contact, req_date, status, comment, _sid = row
        lines = [
            ("Услуга", service),
            ("Клиент", client),
            ("Контакт", contact or "—"),
            ("Дата", fmt_date(req_date)),
            ("Статус", status),
            ("Комментарий", comment or "—"),
        ]
        dialog = ft.AlertDialog(
            title=ft.Text(f"Заявка №{rid}", size=16,
                          weight=ft.FontWeight.BOLD),
            content=ft.Container(
                ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text(label, size=13, color=GREY,
                                        width=100),
                                ft.Text(value, size=13, expand=True),
                            ]
                        )
                        for label, value in lines
                    ],
                    spacing=8,
                ),
                width=340,
            ),
            actions=[
                ft.TextButton("Закрыть",
                              on_click=lambda _: self.page.pop_dialog()),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.show_dialog(dialog)

    def _snack(self, text):
        self.page.show_dialog(
            ft.SnackBar(
                content=ft.Text(text, color=WHITE),
                bgcolor=GREEN,
            )
        )

    # ---------- загрузка данных ----------

    async def _startup(self):
        self.progress.visible = True
        self.page.update()
        try:
            categories = await asyncio.to_thread(db.get_categories)
            self.svc_category.options = [
                ft.DropdownOption(key="", text="Все категории")
            ] + [ft.DropdownOption(key=c, text=c) for c in categories]
            self.online = True
        except Exception:
            self.online = False
        self.progress.visible = False
        self._update_conn_text()
        self.page.update()
        await self.reload_all()
        shots = os.environ.get("CONSALT_SHOTS")
        if shots:
            self.page.run_task(self._take_shots)

    def _update_conn_text(self):
        if self.online:
            self.conn_text.value = "база данных: онлайн"
            self.conn_text.color = ft.Colors.WHITE70
        else:
            self.conn_text.value = "нет связи с базой"
            self.conn_text.color = ft.Colors.RED_100

    async def reload_all(self):
        await self.reload_catalog()
        await self.reload_requests()
        await self.reload_stats()

    async def reload_catalog(self):
        self.progress.visible = True
        self.page.update()
        try:
            rows = await asyncio.to_thread(
                db.list_services,
                search=self.svc_search.value or "",
                category=self.svc_category.value or "",
                status=self.svc_status.value or "",
            )
            total = await asyncio.to_thread(db.count_services)
            self.online = True
        except Exception:
            self.online = False
            self.progress.visible = False
            self._update_conn_text()
            self.page.update()
            return
        self.svc_rows = rows
        self.svc_list.controls = [self._service_card(r) for r in rows]
        self.svc_count.value = f"Показано {len(rows)} из {total}"
        self.progress.visible = False
        self._update_conn_text()
        self.page.update()

    async def reload_requests(self):
        self.progress.visible = True
        self.page.update()
        try:
            rows = await asyncio.to_thread(
                db.list_requests,
                search=self.req_search.value or "",
                status=self.req_status.value or "",
            )
            total = await asyncio.to_thread(db.count_requests)
            self.online = True
        except Exception:
            self.online = False
            self.progress.visible = False
            self._update_conn_text()
            self.page.update()
            return
        self.req_rows = rows
        self.req_list.controls = [self._request_card(r) for r in rows]
        self.req_count.value = f"Показано {len(rows)} из {total}"
        self.progress.visible = False
        self._update_conn_text()
        self.page.update()

    async def reload_stats(self):
        try:
            stats = await asyncio.to_thread(db.summary_stats)
            by_cat = await asyncio.to_thread(db.report_services_by_category)
            self.online = True
        except Exception:
            self.online = False
            self._update_conn_text()
            self.page.update()
            return
        services = stats["services"]
        requests = stats["requests"]
        self.stats_grid.controls = [
            self._stat_box(services[0], "Услуг всего", GREEN),
            self._stat_box(services[1], "Активных",
                           ft.Colors.GREEN_700),
            self._stat_box(requests[0], "Заявок всего", GREEN),
            self._stat_box(requests[1], "Новых",
                           ft.Colors.BLUE),
            self._stat_box(requests[2], "В работе",
                           ft.Colors.ORANGE),
            self._stat_box(requests[3], "Завершено",
                           ft.Colors.GREEN_700),
        ]
        self.stats_categories.controls = [
            ft.Row(
                [
                    ft.Text(name, size=13, expand=True),
                    ft.Text(f"{count} усл.", size=13, color=GREY),
                    ft.Text(f"ср. {fmt_price(avg)} ₽", size=13,
                            color=GREY),
                ]
            )
            for name, count, _mn, _mx, avg in by_cat
        ]
        self.stats_sync.value = (
            f"Синхронизировано с базой в "
            f"{datetime.now().strftime('%H:%M:%S')} — "
            f"те же данные видны в десктоп-приложении"
        )
        self._update_conn_text()
        self.page.update()

    # ---------- скриншоты для отчёта ----------

    async def _take_shots(self):
        out_dir = os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))
        out_dir = os.path.join(out_dir, "report", "images")
        os.makedirs(out_dir, exist_ok=True)
        await asyncio.sleep(1.0)

        async def save(name):
            data = await self.page.take_screenshot(delay=300)
            if not data:
                print("screenshot failed:", name)
                return
            path = os.path.join(out_dir, name)
            with open(path, "wb") as fh:
                fh.write(data)
            print("save:", path)

        await save("mobile_catalog.png")

        if self.svc_rows:
            row = self.svc_rows[1] if len(self.svc_rows) > 1 \
                else self.svc_rows[0]
            await self._on_service_click(_ClickData(row))
            await asyncio.sleep(0.6)
            await save("mobile_service.png")
            self.page.pop_dialog()
            await asyncio.sleep(0.3)
            self._open_request_form(row[0])
            await asyncio.sleep(0.6)
            await save("mobile_request_form.png")
            self.page.pop_dialog()
            await asyncio.sleep(0.3)

        self.nav.selected_index = 1
        self.set_tab(1)
        await asyncio.sleep(0.8)
        await save("mobile_requests.png")

        self.nav.selected_index = 2
        self.set_tab(2)
        await asyncio.sleep(1.0)
        await save("mobile_stats.png")

        await self.page.window.close()


class _ClickData:
    """Мини-заглушка события для автоскриншотов."""

    def __init__(self, row):
        self.control = type("C", (), {"data": row})()


def main(page: ft.Page):
    MobileApp(page)


if __name__ == "__main__":
    ft.run(main)
