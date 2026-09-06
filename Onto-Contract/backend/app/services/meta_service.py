from __future__ import annotations

from flask import current_app

from ..db import get_db


def get_navigation():
    registry = current_app.config["ONTOLOGY_REGISTRY"]
    return registry.navigation


def get_pages():
    registry = current_app.config["ONTOLOGY_REGISTRY"]
    return registry.page_summaries()


def get_page(page_id: str):
    registry = current_app.config["ONTOLOGY_REGISTRY"]
    return registry.pages.get(page_id)


def get_ontology_summary():
    registry = current_app.config["ONTOLOGY_REGISTRY"]
    return registry.ontology_summary()


def get_reference_data():
    db = get_db()
    return {
        "products": db.execute(
            "SELECT id, product_no AS productNo, product_type AS productType, product_name AS productName FROM products ORDER BY product_no"
        ).fetchall(),
        "customers": db.execute(
            "SELECT id, customer_no AS customerNo, customer_type AS customerType, customer_name AS customerName FROM customers ORDER BY customer_no"
        ).fetchall(),
        "departments": db.execute(
            "SELECT id, dept_no AS deptNo, dept_name AS deptName FROM departments ORDER BY dept_no"
        ).fetchall(),
        "employees": db.execute(
            """
            SELECT e.id, e.employee_no AS employeeNo, e.employee_name AS employeeName,
                   e.dept_id AS deptId, d.dept_name AS deptName
            FROM employees e
            JOIN departments d ON d.id = e.dept_id
            ORDER BY e.employee_no
            """
        ).fetchall(),
    }
