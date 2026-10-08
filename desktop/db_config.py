"""Конфигурация подключения к облачной базе данных MySQL (Clever Cloud).

Порядок поиска реквизитов:
1. переменные окружения CC_DB_*;
2. файл .env рядом с .exe (или .env в корне проекта при разработке);
3. встроенные значения по умолчанию (работа без файла .env).
"""
import os
import sys

_DEFAULTS = {
    "CC_DB_HOST": "b9f7wm6ke4johexgbup7-mysql.services.clever-cloud.com",
    "CC_DB_PORT": "3306",
    "CC_DB_USER": "u0ldx0jlewgi7nqr",
    "CC_DB_PASSWORD": "JfyCgmTAsymz6RBQnZhM",
    "CC_DB_NAME": "b9f7wm6ke4johexgbup7",
}

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _env_files():
    paths = []
    if getattr(sys, "frozen", False):
        paths.append(os.path.join(os.path.dirname(sys.executable), ".env"))
    paths.append(os.path.join(_PROJECT_ROOT, ".env"))
    return paths


def _read_env_file(path):
    values = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    values[key.strip()] = val.strip()
    return values


def load_config():
    file_values = {}
    for path in _env_files():
        file_values.update(_read_env_file(path))

    def pick(key):
        return (os.environ.get(key)
                or file_values.get(key)
                or _DEFAULTS.get(key))

    config = {
        "host": pick("CC_DB_HOST"),
        "port": int(pick("CC_DB_PORT") or 3306),
        "user": pick("CC_DB_USER"),
        "password": pick("CC_DB_PASSWORD"),
        "database": pick("CC_DB_NAME"),
        "connection_timeout": 15,
    }
    if not config["host"]:
        raise RuntimeError("Не найдены реквизиты базы данных (файл .env)")
    return config
