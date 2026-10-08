"""Работа с облачной базой данных «КонсалтПро» (MySQL, Clever Cloud)."""
import mysql.connector

from db_config import load_config

SERVICE_SORT = {
    "id": "s.id",
    "category": "c.name",
    "name": "s.name",
    "price": "s.price",
    "unit": "s.unit",
    "duration": "s.duration_days",
    "status": "s.is_active",
}

REQUEST_SORT = {
    "id": "r.id",
    "service": "s.name",
    "client": "r.client_name",
    "contact": "r.contact",
    "date": "r.request_date",
    "status": "r.status",
}


def _connect():
    return mysql.connector.connect(use_pure=True, **load_config())


def ping():
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        return True
    except Exception:
        return False


def _fetch(query, params=()):
    conn = _connect()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        return rows
    finally:
        conn.close()


def _execute(query, params=()):
    conn = _connect()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        row_id = cursor.lastrowid
        cursor.close()
        return row_id
    finally:
        conn.close()


# ---------- справочники ----------

def get_categories():
    return [row[1] for row in _fetch("SELECT id, name FROM categories ORDER BY id")]


def get_service_choices():
    return _fetch(
        "SELECT s.id, CONCAT(s.id, ' — ', s.name) FROM services s ORDER BY s.name"
    )


# ---------- услуги ----------

def count_services():
    return _fetch("SELECT COUNT(*) FROM services")[0][0]


def list_services(search="", category="", unit="", status="",
                  price_min=None, price_max=None,
                  duration_min=None, duration_max=None,
                  sort="id", desc=False):
    query = """
        SELECT s.id, c.name, s.name, s.price, s.unit, s.duration_days, s.is_active
        FROM services s
        JOIN categories c ON c.id = s.category_id
        WHERE 1 = 1
    """
    params = []
    if search:
        query += " AND s.name LIKE %s"
        params.append(f"%{search}%")
    if category and category != "Все категории":
        query += " AND c.name = %s"
        params.append(category)
    if unit and unit != "Все":
        query += " AND s.unit = %s"
        params.append(unit)
    if status and status != "Все":
        query += " AND s.is_active = %s"
        params.append(1 if status == "Активна" else 0)
    if price_min is not None:
        query += " AND s.price >= %s"
        params.append(price_min)
    if price_max is not None:
        query += " AND s.price <= %s"
        params.append(price_max)
    if duration_min is not None:
        query += " AND s.duration_days >= %s"
        params.append(duration_min)
    if duration_max is not None:
        query += " AND s.duration_days <= %s"
        params.append(duration_max)
    order = SERVICE_SORT.get(sort, "s.id")
    query += f" ORDER BY {order} {'DESC' if desc else 'ASC'}"
    return _fetch(query, params)


def add_service(category, name, description, price, unit, duration, is_active):
    cat_id = _fetch("SELECT id FROM categories WHERE name = %s", (category,))[0][0]
    return _execute(
        """INSERT INTO services
           (category_id, name, description, price, unit, duration_days, is_active)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (cat_id, name, description, price, unit, duration, is_active),
    )


def update_service(service_id, category, name, description, price, unit,
                   duration, is_active):
    cat_id = _fetch("SELECT id FROM categories WHERE name = %s", (category,))[0][0]
    _execute(
        """UPDATE services
           SET category_id = %s, name = %s, description = %s, price = %s,
               unit = %s, duration_days = %s, is_active = %s
           WHERE id = %s""",
        (cat_id, name, description, price, unit, duration, is_active, service_id),
    )


def delete_service(service_id):
    _execute("DELETE FROM services WHERE id = %s", (service_id,))


def get_service(service_id):
    rows = _fetch(
        """SELECT s.category_id, c.name, s.name, s.description, s.price,
                  s.unit, s.duration_days, s.is_active
           FROM services s JOIN categories c ON c.id = s.category_id
           WHERE s.id = %s""",
        (service_id,),
    )
    return rows[0] if rows else None


# ---------- заявки ----------

def count_requests():
    return _fetch("SELECT COUNT(*) FROM requests")[0][0]


def list_requests(status="", date_from=None, date_to=None, search="",
                  sort="date", desc=True):
    query = """
        SELECT r.id, s.name, r.client_name, r.contact, r.request_date,
               r.status, r.comment, r.service_id
        FROM requests r
        JOIN services s ON s.id = r.service_id
        WHERE 1 = 1
    """
    params = []
    if status and status != "Все статусы":
        query += " AND r.status = %s"
        params.append(status)
    if date_from:
        query += " AND r.request_date >= %s"
        params.append(date_from)
    if date_to:
        query += " AND r.request_date <= %s"
        params.append(date_to)
    if search:
        query += " AND (r.client_name LIKE %s OR s.name LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%"])
    order = REQUEST_SORT.get(sort, "r.request_date")
    query += f" ORDER BY {order} {'DESC' if desc else 'ASC'}, r.id DESC"
    return _fetch(query, params)


def add_request(service_id, client_name, contact, request_date, status, comment):
    return _execute(
        """INSERT INTO requests
           (service_id, client_name, contact, request_date, status, comment)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (service_id, client_name, contact, request_date, status, comment),
    )


def update_request(request_id, service_id, client_name, contact, request_date,
                   status, comment):
    _execute(
        """UPDATE requests
           SET service_id = %s, client_name = %s, contact = %s,
               request_date = %s, status = %s, comment = %s
           WHERE id = %s""",
        (service_id, client_name, contact, request_date, status, comment, request_id),
    )


def delete_request(request_id):
    _execute("DELETE FROM requests WHERE id = %s", (request_id,))


def get_request(request_id):
    rows = _fetch(
        """SELECT service_id, client_name, contact, request_date, status, comment
           FROM requests WHERE id = %s""",
        (request_id,),
    )
    return rows[0] if rows else None


# ---------- отчёты ----------

def report_services_by_category():
    return _fetch(
        """SELECT c.name, COUNT(s.id), MIN(s.price), MAX(s.price),
                  ROUND(AVG(s.price))
           FROM categories c
           LEFT JOIN services s ON s.category_id = c.id
           GROUP BY c.id, c.name
           ORDER BY c.id"""
    )


def report_requests_period(date_from, date_to):
    return _fetch(
        """SELECT r.id, s.name, r.client_name, r.request_date, r.status
           FROM requests r
           JOIN services s ON s.id = r.service_id
           WHERE r.request_date BETWEEN %s AND %s
           ORDER BY r.request_date, r.id""",
        (date_from, date_to),
    )


def report_revenue_by_category(date_from, date_to):
    return _fetch(
        """SELECT c.name, COUNT(r.id), COALESCE(SUM(s.price), 0)
           FROM categories c
           LEFT JOIN services s ON s.category_id = c.id
           LEFT JOIN requests r ON r.service_id = s.id
               AND r.status = 'Завершена'
               AND r.request_date BETWEEN %s AND %s
           GROUP BY c.id, c.name
           ORDER BY c.id""",
        (date_from, date_to),
    )


def summary_stats():
    services = _fetch(
        """SELECT COUNT(*), SUM(is_active = 1), SUM(is_active = 0)
           FROM services"""
    )[0]
    requests = _fetch(
        """SELECT COUNT(*), SUM(status = 'Новая'), SUM(status = 'В работе'),
                  SUM(status = 'Завершена'), SUM(status = 'Отменена')
           FROM requests"""
    )[0]
    return {"services": services, "requests": requests}
