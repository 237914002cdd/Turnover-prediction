"""
SQLite 数据库连接与查询工具
所有路由通过此模块读取 turnover.db
"""

import sqlite3
import os

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(_PROJECT_ROOT, "turnover.db")


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def find_employee(employee_id_hash: str) -> dict:
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM employees WHERE employee_id_hash = ?", (employee_id_hash,)
    ).fetchone()
    conn.close()
    if row is None:
        return None
    return dict(row)


def get_top_hubs(limit: int = 100) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT employee_id_hash, department_cn, job_role_cn, monthly_income, "
        "ona_eigenvector_centrality, risk_level, performance_level, "
        "attrition_cn, performance_cn "
        "FROM employees ORDER BY ona_eigenvector_centrality DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_neighbors(employee_id_hash: str, depth: int = 2) -> tuple[list[dict], list[dict]]:
    conn = get_conn()

    center = conn.execute(
        "SELECT * FROM employees WHERE employee_id_hash = ?", (employee_id_hash,)
    ).fetchone()
    if center is None:
        conn.close()
        return [], []

    center = dict(center)
    visited = {employee_id_hash}
    nodes_map = {employee_id_hash: center}
    edges = []
    queue = [(employee_id_hash, 0)]

    while queue:
        current_id, level = queue.pop(0)
        if level >= depth:
            continue

        current = nodes_map[current_id]
        dept = current.get("department_cn", "")
        ec = current.get("ona_eigenvector_centrality", 0)

        neighbors = conn.execute(
            "SELECT * FROM employees WHERE department_cn = ? AND employee_id_hash != ? "
            "ORDER BY ona_eigenvector_centrality DESC LIMIT 20",
            (dept, current_id),
        ).fetchall()

        for nb in neighbors:
            nb = dict(nb)
            nid = nb["employee_id_hash"]
            if nid not in visited:
                visited.add(nid)
                nodes_map[nid] = nb
                if level + 1 <= depth:
                    queue.append((nid, level + 1))
            edges.append({"source": current_id, "target": nid})

        if ec > 0.05:
            cross = conn.execute(
                "SELECT * FROM employees WHERE department_cn != ? AND ona_eigenvector_centrality > 0.05 "
                "ORDER BY ona_eigenvector_centrality DESC LIMIT 5",
                (dept,),
            ).fetchall()
            for nb in cross:
                nb = dict(nb)
                nid = nb["employee_id_hash"]
                if nid not in visited:
                    visited.add(nid)
                    nodes_map[nid] = nb
                    edges.append({"source": current_id, "target": nid})

    conn.close()
    nodes = [v for k, v in nodes_map.items()]
    return nodes, edges
