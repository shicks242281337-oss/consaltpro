"""Создание и наполнение базы данных «КонсалтПро»."""
import os
import sys

import mysql.connector

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_config():
    values = {}
    path = os.path.join(BASE_DIR, ".env")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    values[key.strip()] = val.strip()
    return {
        "host": values.get("CC_DB_HOST"),
        "port": int(values.get("CC_DB_PORT") or 3306),
        "user": values.get("CC_DB_USER"),
        "password": values.get("CC_DB_PASSWORD"),
        "database": values.get("CC_DB_NAME"),
        "connection_timeout": 15,
    }


def run_file(cursor, path):
    with open(path, encoding="utf-8") as fh:
        script = fh.read()
    for statement in script.split(";"):
        statement = statement.strip()
        if statement:
            cursor.execute(statement)


def main():
    fresh = "--fresh" in sys.argv[1:]
    base = os.path.dirname(os.path.abspath(__file__))
    conn = mysql.connector.connect(**load_config())
    cursor = conn.cursor()
    if fresh:
        for table in ("requests", "services", "clients", "categories"):
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
        conn.commit()
    run_file(cursor, os.path.join(base, "schema.sql"))
    conn.commit()
    run_file(cursor, os.path.join(base, "seed.sql"))
    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM categories")
    cats = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM services")
    services = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM requests")
    requests = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    print(f"База готова: категорий — {cats}, услуг — {services}, заявок — {requests}")


if __name__ == "__main__":
    main()
