"""Конфигурация подключения к облачной MySQL для мобильного приложения.

В APK файл .env отсутствует, поэтому реквизиты продублированы здесь
и могут быть переопределены переменными окружения CC_DB_*.
"""
import os

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_DEFAULTS = {
    "CC_DB_HOST": "b9f7wm6ke4johexgbup7-mysql.services.clever-cloud.com",
    "CC_DB_PORT": "3306",
    "CC_DB_USER": "u0ldx0jlewgi7nqr",
    "CC_DB_PASSWORD": "JfyCgmTAsymz6RBQnZhM",
    "CC_DB_NAME": "b9f7wm6ke4johexgbup7",
}


def _read_env_file():
    values = {}
    path = os.path.join(_BASE_DIR, ".env")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    values[key.strip()] = val.strip()
    return values


def load_config():
    file_values = _read_env_file()

    def pick(key):
        return (os.environ.get(key)
                or file_values.get(key)
                or _DEFAULTS.get(key))

    return {
        "host": pick("CC_DB_HOST"),
        "port": int(pick("CC_DB_PORT") or 3306),
        "user": pick("CC_DB_USER"),
        "password": pick("CC_DB_PASSWORD"),
        "database": pick("CC_DB_NAME"),
        "connection_timeout": 15,
    }
