"""Функциональные тесты слоя работы с базой данных.

Запуск: python test_db.py
"""
import unittest
from datetime import date

import db


class ServiceFiltersTest(unittest.TestCase):
    """Каждый фильтр должен возвращать не менее 5 строк."""

    def test_total_at_least_100(self):
        self.assertGreaterEqual(db.count_services(), 100)

    def test_filter_by_category(self):
        for category in db.get_categories():
            rows = db.list_services(category=category)
            self.assertGreaterEqual(len(rows), 5, category)
            for row in rows:
                self.assertEqual(row[1], category)

    def test_filter_by_unit(self):
        for unit in ("проект", "час", "день", "месяц"):
            rows = db.list_services(unit=unit)
            self.assertGreaterEqual(len(rows), 5, unit)
            for row in rows:
                self.assertEqual(row[4], unit)

    def test_filter_by_status(self):
        active = db.list_services(status="Активна")
        inactive = db.list_services(status="Неактивна")
        self.assertGreaterEqual(len(active), 5)
        self.assertGreaterEqual(len(inactive), 5)

    def test_filter_by_price_ranges(self):
        ranges = [
            (None, 50000), (50001, 100000), (100001, 150000),
            (150001, 200000), (200001, None),
        ]
        for low, high in ranges:
            rows = db.list_services(price_min=low, price_max=high)
            self.assertGreaterEqual(len(rows), 5, f"{low}-{high}")

    def test_filter_by_duration_ranges(self):
        ranges = [
            (None, 7), (8, 14), (15, 21), (22, 30), (31, None),
        ]
        for low, high in ranges:
            rows = db.list_services(duration_min=low, duration_max=high)
            self.assertGreaterEqual(len(rows), 5, f"{low}-{high}")

    def test_search_by_name(self):
        rows = db.list_services(search="Аудит")
        self.assertGreaterEqual(len(rows), 5)
        for row in rows:
            self.assertIn("аудит", row[2].lower())

    def test_sorting_by_price(self):
        rows = db.list_services(sort="price", desc=True)
        prices = [row[3] for row in rows]
        self.assertEqual(prices, sorted(prices, reverse=True))


class RequestFiltersTest(unittest.TestCase):
    def test_statuses(self):
        for status in ("Новая", "В работе", "Завершена", "Отменена"):
            rows = db.list_requests(status=status)
            self.assertGreaterEqual(len(rows), 5, status)

    def test_date_period(self):
        rows = db.list_requests(
            date_from=date(2026, 9, 1), date_to=date(2026, 9, 30))
        self.assertGreaterEqual(len(rows), 5)
        for row in rows:
            self.assertEqual(row[4].month, 9)

    def test_search(self):
        rows = db.list_requests(search="Вектор")
        self.assertGreaterEqual(len(rows), 1)


class CrudTest(unittest.TestCase):
    """Проверка добавления, редактирования и удаления записей."""

    def test_service_crud(self):
        categories = db.get_categories()
        new_id = db.add_service(
            categories[0], "ТЕСТ-услуга", "Тестовая запись",
            12345.0, "час", 3, 1)
        try:
            row = db.get_service(new_id)
            self.assertEqual(row[2], "ТЕСТ-услуга")
            db.update_service(
                new_id, categories[1], "ТЕСТ-услуга 2", "Обновлено",
                54321.0, "день", 7, 0)
            row = db.get_service(new_id)
            self.assertEqual(row[2], "ТЕСТ-услуга 2")
            self.assertEqual(row[7], 0)
        finally:
            db.delete_service(new_id)
        self.assertIsNone(db.get_service(new_id))

    def test_request_crud(self):
        choices = db.get_service_choices()
        service_id = choices[0][0]
        new_id = db.add_request(
            service_id, "ТЕСТ-Клиент", "test@mail.ru",
            date(2026, 10, 1), "Новая", "тест")
        try:
            row = db.get_request(new_id)
            self.assertEqual(row[1], "ТЕСТ-Клиент")
            db.update_request(
                new_id, service_id, "ТЕСТ-Клиент 2", "+7 000 000-00-00",
                date(2026, 10, 2), "В работе", "обновлено")
            row = db.get_request(new_id)
            self.assertEqual(row[1], "ТЕСТ-Клиент 2")
            self.assertEqual(row[4], "В работе")
        finally:
            db.delete_request(new_id)
        self.assertIsNone(db.get_request(new_id))


class ReportsTest(unittest.TestCase):
    def test_reports_return_rows(self):
        self.assertGreaterEqual(len(db.report_services_by_category()), 5)
        period = db.report_requests_period(date(2026, 8, 15), date(2026, 10, 8))
        self.assertGreaterEqual(len(period), 40)
        revenue = db.report_revenue_by_category(date(2026, 8, 15), date(2026, 10, 8))
        self.assertGreaterEqual(len(revenue), 5)

    def test_ping(self):
        self.assertTrue(db.ping())


if __name__ == "__main__":
    unittest.main(verbosity=2)
