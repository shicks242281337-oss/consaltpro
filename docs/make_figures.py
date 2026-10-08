"""Генерация рисунков для отчёта (схемы, эскизы, палитра).

Запуск: python make_figures.py
"""
import os

from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "report", "images")
os.makedirs(OUT, exist_ok=True)

GREEN_DARK = (27, 94, 32)
GREEN = (46, 125, 50)
GREEN_LIGHT = (238, 246, 238)
GREY = (92, 102, 96)
GREY_LIGHT = (240, 242, 240)
INK = (28, 35, 33)
BLUE = (33, 150, 243)
ORANGE = (245, 124, 0)
RED = (198, 40, 40)
WHITE = (255, 255, 255)

FONT = r"C:\Windows\Fonts\arial.ttf"
FONT_B = r"C:\Windows\Fonts\arialbd.ttf"


def f(size):
    return ImageFont.truetype(FONT, size)


def fb(size):
    return ImageFont.truetype(FONT_B, size)


def arrow(d, x1, y1, x2, y2, color=GREY, width=3):
    d.line((x1, y1, x2, y2), fill=color, width=width)
    import math
    ang = math.atan2(y2 - y1, x2 - x1)
    ln = 12
    for delta in (2.6, -2.6):
        d.line((x2, y2,
                x2 - ln * math.cos(ang + delta),
                y2 - ln * math.sin(ang + delta)),
               fill=color, width=width)


def box(d, xy, title, sub=None, fill=WHITE, outline=GREEN, title_color=None,
        title_font=None, sub_font=None, radius=10, pad=6):
    x1, y1, x2, y2 = xy
    d.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=3)
    title_font = title_font or fb(22)
    sub_font = sub_font or f(17)
    tc = title_color or GREEN_DARK
    if sub is not None:
        d.text(((x1 + x2) / 2, y1 + 26), title, font=title_font, fill=tc,
               anchor="mm")
        for i, line in enumerate(sub):
            d.text(((x1 + x2) / 2, y1 + 66 + i * 24), line, font=sub_font,
                   fill=INK, anchor="mm")
    else:
        d.text(((x1 + x2) / 2, (y1 + y2) / 2), title, font=title_font,
               fill=tc, anchor="mm")


def canvas(w, h):
    im = Image.new("RGB", (w, h), WHITE)
    return im, ImageDraw.Draw(im)


# ---------------------------------------------------------------- архитектура

def arch_desktop():
    im, d = canvas(1240, 640)
    d.text((620, 34), "Архитектура десктопного приложения", font=fb(28),
           fill=GREEN_DARK, anchor="mm")

    box(d, (40, 275, 210, 395), "Пользователь",
        ["оператор", "компании"], fill=GREY_LIGHT, outline=GREY,
        title_color=INK)

    box(d, (280, 150, 700, 500), "Десктопное приложение «КонсалтПро»",
        [], fill=WHITE, outline=GREEN)
    box(d, (310, 215, 670, 335), "Пользовательский интерфейс",
        ["CustomTkinter: вкладки, таблицы,", "фильтры, диалоговые формы"],
        fill=GREEN_LIGHT, outline=GREEN)
    box(d, (310, 375, 670, 485), "Слой доступа к данным",
        ["db.py: запросы, фильтры, CRUD,", "отчёты (mysql-connector)"],
        fill=GREEN_LIGHT, outline=GREEN)

    box(d, (780, 60, 1200, 170), "Облачная база данных MySQL",
        ["Clever Cloud: каталог, заявки"], fill=WHITE, outline=BLUE,
        title_color=(13, 71, 161))
    box(d, (780, 230, 1200, 330), "Файлы отчётов",
        ["Excel (openpyxl) и TXT"], fill=WHITE, outline=ORANGE,
        title_color=(180, 80, 0))
    box(d, (780, 400, 1200, 510), "Сборка PyInstaller",
        ["ConsaltPro.exe (~35 МБ),", "запуск без установки"],
        fill=GREY_LIGHT, outline=GREY, title_color=INK)

    arrow(d, 210, 335, 280, 335)
    arrow(d, 490, 335, 490, 375)
    arrow(d, 670, 275, 780, 130)
    arrow(d, 670, 430, 780, 280)
    arrow(d, 490, 500, 780, 460)
    im.save(os.path.join(OUT, "fig_arch_desktop.png"))


def arch_mobile():
    im, d = canvas(1240, 560)
    d.text((620, 34), "Архитектура мобильного приложения", font=fb(28),
           fill=GREEN_DARK, anchor="mm")

    box(d, (40, 245, 210, 365), "Пользователь",
        ["клиент или", "менеджер"], fill=GREY_LIGHT, outline=GREY,
        title_color=INK)

    box(d, (280, 130, 700, 495), "Мобильное приложение «КонсалтПро»",
        [], fill=WHITE, outline=GREEN)
    box(d, (310, 195, 670, 315), "Интерфейс Flet",
        ["Каталог · Заявки · Статистика,", "поиск и фильтры, форма заявки"],
        fill=GREEN_LIGHT, outline=GREEN)
    box(d, (310, 345, 670, 465), "Слой доступа к данным",
        ["db.py: те же запросы,", "что и в десктоп-версии"],
        fill=GREEN_LIGHT, outline=GREEN)

    box(d, (780, 80, 1200, 190), "Облачная база данных MySQL",
        ["Clever Cloud — общая с ПК"], fill=WHITE, outline=BLUE,
        title_color=(13, 71, 161))
    box(d, (780, 250, 1200, 360), "Синхронизация",
        ["заявка на телефоне сразу", "видна на ПК и наоборот"],
        fill=GREEN_LIGHT, outline=GREEN)
    box(d, (780, 420, 1200, 530), "Сборка Flet",
        ["ConsaltPro.apk (~68 МБ),", "установка на Android"],
        fill=GREY_LIGHT, outline=GREY, title_color=INK)

    arrow(d, 210, 305, 280, 305)
    arrow(d, 490, 315, 490, 345)
    arrow(d, 670, 255, 780, 150)
    arrow(d, 670, 405, 780, 305)
    arrow(d, 490, 495, 780, 470)
    im.save(os.path.join(OUT, "fig_arch_mobile.png"))


def site_structure():
    im, d = canvas(1240, 620)
    d.text((620, 34), "Логическая структура сайта-загрузчика", font=fb(28),
           fill=GREEN_DARK, anchor="mm")

    box(d, (400, 90, 840, 180), "index.html — главная страница",
        ["герой, возможности, скриншоты, блок «Скачать»"],
        fill=WHITE, outline=GREEN)

    box(d, (60, 290, 380, 390), "assets/style.css",
        ["оформление, адаптив"], fill=GREEN_LIGHT, outline=GREEN)
    box(d, (430, 290, 750, 390), "assets/app.js",
        ["ссылки на релизы, версия"], fill=GREEN_LIGHT, outline=GREEN)
    box(d, (800, 290, 1180, 390), "assets/*.png",
        ["скриншоты приложений"], fill=GREEN_LIGHT, outline=GREEN)

    box(d, (250, 470, 640, 560), "GitHub Releases",
        ["ConsaltPro.exe, ConsaltPro.apk"], fill=WHITE, outline=BLUE,
        title_color=(13, 71, 161))
    box(d, (720, 470, 1140, 560), "GitHub REST API",
        ["номер последней версии"], fill=WHITE, outline=ORANGE,
        title_color=(180, 80, 0))

    arrow(d, 330, 300, 430, 190)
    arrow(d, 590, 300, 590, 190)
    arrow(d, 990, 300, 760, 190)
    arrow(d, 500, 390, 460, 470)
    arrow(d, 600, 390, 830, 470)
    im.save(os.path.join(OUT, "fig_site_structure.png"))


# ------------------------------------------------------------------ ER-схема

def er_diagram():
    im, d = canvas(1240, 760)
    d.text((620, 34), "Структура базы данных «КонсалтПро»", font=fb(28),
           fill=GREEN_DARK, anchor="mm")

    def table(x, y, w, name, fields, h_header=42, row_h=26):
        h = h_header + row_h * len(fields) + 8
        d.rectangle((x, y, x + w, y + h), fill=WHITE, outline=GREY, width=2)
        d.rectangle((x, y, x + w, y + h_header), fill=GREEN_DARK)
        d.text((x + w / 2, y + h_header / 2), name, font=fb(20), fill=WHITE,
               anchor="mm")
        for i, (fld, key) in enumerate(fields):
            yy = y + h_header + 6 + row_h * i + row_h / 2
            color = GREEN_DARK if key == "PK" else INK
            prefix = "PK" if key == "PK" else ("FK" if key == "FK" else "")
            d.text((x + 12, yy), prefix, font=fb(14), fill=ORANGE,
                   anchor="lm")
            d.text((x + 44, yy), fld, font=f(16), fill=color, anchor="lm")
        return h

    h1 = table(60, 110, 330, "categories",
               [("id", "PK"), ("name  UNIQUE", "")])
    table(60, 430, 330, "clients",
          [("id", "PK"), ("name", ""), ("phone", ""), ("email", "")])

    h2 = table(470, 110, 360, "services",
               [("id", "PK"), ("category_id", "FK"), ("name", ""),
                ("description", ""), ("price", ""), ("unit", ""),
                ("duration_days", ""), ("is_active", "")])

    table(870, 240, 330, "requests",
          [("id", "PK"), ("service_id", "FK"), ("client_name", ""),
           ("contact", ""), ("request_date", ""), ("status", ""),
           ("comment", "")])

    arrow(d, 390, 110 + h1 // 2, 470, 110 + 70, color=GREEN, width=3)
    arrow(d, 830, 110 + h2 // 2, 870, 300, color=GREEN, width=3)

    d.text((425, 150), "1 : N", font=fb(16), fill=GREY, anchor="mm")
    d.text((850, 215), "1 : N", font=fb(16), fill=GREY, anchor="mm")
    d.text((225, 600), "справочник клиентов (резерв);",
           font=f(16), fill=GREY, anchor="mm")
    d.text((225, 624), "в заявке хранится имя клиента",
           font=f(16), fill=GREY, anchor="mm")
    im.save(os.path.join(OUT, "fig_er.png"))


# --------------------------------------------------------------- цветовая схема

def palette():
    im, d = canvas(1240, 430)
    d.text((620, 34), "Цветовая схема приложения", font=fb(28),
           fill=GREEN_DARK, anchor="mm")

    main_colors = [
        ("#1B5E20", "основной", GREEN_DARK),
        ("#2E7D32", "кнопки, шапка", GREEN),
        ("#43A047", "акцент", (67, 160, 71)),
        ("#EEF6EE", "фон", GREEN_LIGHT),
        ("#FFFFFF", "карточки", WHITE),
        ("#1C2321", "текст", INK),
        ("#5C6660", "вторичный текст", GREY),
    ]
    status = [
        ("#2196F3", "Новая", BLUE),
        ("#F57C00", "В работе", ORANGE),
        ("#2E7D32", "Завершена", GREEN),
        ("#C62828", "Отменена", RED),
    ]

    x = 60
    for hexv, label, color in main_colors:
        d.rounded_rectangle((x, 90, x + 140, 210), radius=8, fill=color,
                            outline=GREY, width=1)
        d.text((x + 70, 235), hexv, font=fb(17), fill=INK, anchor="mm")
        d.text((x + 70, 262), label, font=f(15), fill=GREY, anchor="mm")
        x += 165

    x = 60
    d.text((60, 296), "Статусы заявок:", font=fb(19), fill=GREEN_DARK,
           anchor="lm")
    for hexv, label, color in status:
        d.rounded_rectangle((x, 316, x + 46, 362), radius=8, fill=color,
                            outline=GREY, width=1)
        d.text((x + 60, 339), f"{label} — {hexv}", font=f(17), fill=INK,
               anchor="lm")
        x += 240
    im.save(os.path.join(OUT, "fig_palette.png"))


# --------------------------------------------------------------------- эскизы

def sketch_desktop():
    im, d = canvas(1240, 760)
    d.text((620, 30), "Эскиз главного окна десктопного приложения",
           font=fb(26), fill=GREEN_DARK, anchor="mm")

    d.rounded_rectangle((40, 70, 1200, 730), radius=10, fill=WHITE,
                        outline=GREY, width=3)
    d.rectangle((40, 70, 1200, 130), fill=GREEN_DARK)
    d.text((70, 100), "КонсалтПро — панель консалтинговых услуг",
           font=fb(22), fill=WHITE, anchor="lm")
    d.rounded_rectangle((1010, 82, 1180, 118), radius=6, fill=GREEN)
    d.text((1095, 100), "Обновить данные", font=f(15), fill=WHITE,
           anchor="mm")

    tabs = [("Услуги", True), ("Заявки", False), ("Отчёты", False)]
    x = 480
    for name, active in tabs:
        w = 120
        d.rectangle((x, 145, x + w, 180), fill=GREEN if active else GREY_LIGHT,
                    outline=GREY)
        d.text((x + w / 2, 162), name, font=f(16),
               fill=WHITE if active else INK, anchor="mm")
        x += w

    d.rounded_rectangle((60, 200, 300, 700), radius=8, fill=GREY_LIGHT,
                        outline=GREY)
    d.text((180, 228), "Фильтры", font=fb(20), fill=GREEN_DARK, anchor="mm")
    y = 258
    for label in ["Название (поиск)", "Категория", "Единица измерения",
                  "Статус", "Цена, ₽ от … до", "Срок, дни от … до"]:
        d.text((75, y), label, font=f(14), fill=GREY, anchor="lm")
        d.rectangle((75, y + 8, 285, y + 38), fill=WHITE, outline=GREY)
        y += 54
    d.rectangle((75, 588, 285, 628), fill=GREEN)
    d.text((180, 608), "Применить", font=f(15), fill=WHITE, anchor="mm")
    d.rectangle((75, 640, 285, 680), fill=GREY)
    d.text((180, 660), "Сбросить", font=f(15), fill=WHITE, anchor="mm")

    for i, (label, color) in enumerate([("Добавить", GREEN),
                                        ("Изменить", ORANGE),
                                        ("Удалить", RED)]):
        x0 = 320 + i * 150
        d.rectangle((x0, 200, x0 + 135, 240), fill=color)
        d.text((x0 + 67, 220), label, font=f(16), fill=WHITE, anchor="mm")

    headers = ["ID", "Категория", "Название", "Цена", "Ед.", "Срок",
               "Статус"]
    widths = [45, 150, 280, 90, 70, 70, 90]
    x, y = 320, 260
    for name, w in zip(headers, widths):
        d.rectangle((x, y, x + w, y + 36), fill=GREEN_LIGHT, outline=GREY)
        d.text((x + w / 2, y + 18), name, font=fb(14), fill=INK, anchor="mm")
        x += w
    for row in range(7):
        x = 320
        y = 296 + row * 44
        for w in widths:
            d.rectangle((x, y, x + w, y + 44), fill=WHITE, outline=GREY)
            x += w
        d.line((330, y + 22, 330 + widths[0] - 20, y + 22), fill=GREY_LIGHT,
               width=6)

    d.text((470, 630), "Показано 110 из 110", font=f(15), fill=GREY,
           anchor="lm")
    d.line((320, 700, 1180, 700), fill=GREY, width=2)
    d.text((330, 715), "База данных: подключено", font=f(14), fill=GREY,
           anchor="lm")
    im.save(os.path.join(OUT, "fig_sketch_desktop.png"))


def phone_frame(d, w=470, h=900):
    d.rounded_rectangle((0, 0, w, h), radius=30, fill=WHITE, outline=INK,
                        width=4)
    d.rectangle((w // 2 - 60, 12, w // 2 + 60, 30), fill=INK)


def sketch_mobile():
    im, d = canvas(500, 940)
    d.text((250, 24), "Эскиз каталога (мобильное)", font=fb(24),
           fill=GREEN_DARK, anchor="mm")
    im2 = Image.new("RGB", (470, 860), WHITE)
    d2 = ImageDraw.Draw(im2)

    d2.rectangle((0, 0, 470, 100), fill=GREEN_DARK)
    d2.text((24, 38), "КонсалтПро", font=fb(26), fill=WHITE, anchor="lm")
    d2.text((24, 72), "каталог услуг и заявки", font=f(15),
            fill=(200, 220, 200), anchor="lm")
    d2.ellipse((410, 30, 450, 70), outline=WHITE, width=3)

    d2.rounded_rectangle((16, 116, 454, 250), radius=14, fill=GREY_LIGHT,
                         outline=GREY)
    d2.rectangle((34, 132, 436, 172), fill=WHITE, outline=GREY)
    d2.text((50, 152), "Поиск по названию…", font=f(17), fill=GREY,
            anchor="lm")
    d2.rectangle((34, 190, 232, 234), fill=WHITE, outline=GREY)
    d2.text((46, 204), "Категория", font=f(13), fill=GREY, anchor="lm")
    d2.text((46, 222), "Все категории", font=f(16), fill=INK, anchor="lm")
    d2.rectangle((244, 190, 436, 234), fill=WHITE, outline=GREY)
    d2.text((256, 204), "Статус", font=f(13), fill=GREY, anchor="lm")
    d2.text((256, 222), "Все", font=f(16), fill=INK, anchor="lm")

    d2.text((24, 276), "Показано 110 из 110", font=f(15), fill=GREY,
            anchor="lm")
    y = 300
    for i in range(6):
        d2.rounded_rectangle((16, y, 454, y + 96), radius=14, fill=WHITE,
                             outline=GREY)
        d2.rectangle((34, y + 34, 66, y + 66), outline=GREEN, width=3)
        d2.text((84, y + 32), "Название услуги", font=fb(17), fill=INK,
                anchor="lm")
        d2.text((84, y + 60), "Категория • 55 000 ₽ • 25 дн.", font=f(14),
                fill=GREY, anchor="lm")
        d2.text((430, y + 48), "›", font=f(26), fill=GREY, anchor="mm")
        y += 108

    d2.rectangle((0, 790, 470, 860), fill=WHITE, outline=GREY)
    for i, (name, active) in enumerate([("Каталог", True), ("Заявки", False),
                                        ("Статистика", False)]):
        x = 78 + i * 158
        d2.ellipse((x - 22, 802, x + 22, 846),
                   fill=GREEN_LIGHT if active else WHITE, outline=GREY)
        d2.text((x, 855), name, font=f(13),
                fill=GREEN_DARK if active else GREY, anchor="mm")

    im.paste(im2, (15, 55))
    im.save(os.path.join(OUT, "fig_sketch_mobile.png"))


def sketch_request():
    im, d = canvas(500, 940)
    d.text((250, 24), "Эскиз формы заявки (мобильное)", font=fb(24),
           fill=GREEN_DARK, anchor="mm")
    im2 = Image.new("RGB", (470, 860), (225, 230, 225))
    d2 = ImageDraw.Draw(im2)

    d2.rectangle((0, 0, 470, 80), fill=GREEN_DARK)
    d2.text((24, 40), "КонсалтПро", font=fb(24), fill=WHITE, anchor="lm")
    for i in range(4):
        d2.rounded_rectangle((16, 100 + i * 120, 454, 196 + i * 120),
                             radius=14, fill=WHITE, outline=GREY)

    d2.rounded_rectangle((36, 150, 434, 720), radius=18, fill=WHITE,
                         outline=GREY, width=3)
    d2.text((64, 196), "Новая заявка", font=fb(24), fill=INK, anchor="lm")
    y = 250
    for label, h in [("Ваше имя *", 60), ("Телефон или e-mail", 60),
                     ("Дата заявки", 60), ("Комментарий", 120)]:
        d2.rectangle((64, y, 406, y + h), fill=WHITE, outline=GREY, width=2)
        d2.text((80, y + h // 2), label, font=f(17), fill=GREY, anchor="lm")
        y += h + 28

    d2.rounded_rectangle((170, 630, 300, 684), radius=12, fill=GREEN)
    d2.text((235, 657), "Отправить", font=fb(18), fill=WHITE, anchor="mm")
    d2.text((110, 657), "Отмена", font=f(18), fill=GREY, anchor="mm")

    im.paste(im2, (15, 55))
    im.save(os.path.join(OUT, "fig_sketch_request.png"))


if __name__ == "__main__":
    arch_desktop()
    arch_mobile()
    site_structure()
    er_diagram()
    palette()
    sketch_desktop()
    sketch_mobile()
    sketch_request()
    print("figures saved to", OUT)
