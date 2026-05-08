"""Smoke tests for the public catalog endpoints."""
from odoo.tests import HttpCase, tagged


@tagged("tezz_api", "post_install", "-at_install")
class TestCatalog(HttpCase):

    def test_home_public(self):
        r = self.url_open("/api/v1/home")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("trending", body["data"])
        self.assertIn("categories", body["data"])

    def test_categories_public(self):
        r = self.url_open("/api/v1/categories")
        self.assertEqual(r.status_code, 200)
        self.assertIn("categories", r.json()["data"])

    def test_products_pagination(self):
        r = self.url_open("/api/v1/products?page=1&page_size=5")
        self.assertEqual(r.status_code, 200)
        meta = r.json()["meta"]
        self.assertEqual(meta["page"], 1)
        self.assertEqual(meta["page_size"], 5)
        self.assertIn("total", meta)

    def test_search_requires_query(self):
        r = self.url_open("/api/v1/products/search?q=a")
        self.assertEqual(r.status_code, 400)

    def test_protected_route_requires_token(self):
        r = self.url_open("/api/v1/cart")
        self.assertEqual(r.status_code, 401)
