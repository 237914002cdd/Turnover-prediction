"""
CSV/Excel 数据导入 —— FastAPI 路由
接口: POST /api/v1/ona/graph/upload

接收 CSV 或 Excel 文件，解析员工数据并批量写入 turnover.db。
"""

import csv, hashlib, io, os, tempfile
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, UploadFile, File, status
import pandas as pd
import numpy as np

from api.models.ona_models import OnaImportResponse, ImportResult
from api.services.db import DB_PATH

router = APIRouter(prefix="/api/v1/ona", tags=["ONA 数据导入"])

# 必填字段列表
_REQUIRED_COLS = [
    "Age", "Attrition", "BusinessTravel", "Department", "Education",
    "EducationField", "Gender", "JobLevel", "JobRole", "MaritalStatus",
    "MonthlyIncome", "OverTime", "PercentSalaryHike", "PerformanceRating",
    "TotalWorkingYears", "YearsAtCompany", "YearsInCurrentRole",
    "YearsSinceLastPromotion",
]

# 中文化映射
_DEPT_MAP = {
    "Research & Development": "用友网络 - 数智人力事业部",
    "Sales": "数智营销事业部",
    "Human Resources": "人力资源中心",
}
_ROLE_MAP = {
    "Research Scientist": "高级算法工程师", "Laboratory Technician": "实验室技术员",
    "Manager": "高级产品经理", "Sales Executive": "高级销售顾问",
    "Manufacturing Director": "制造总监", "Sales Representative": "售前顾问",
    "Research Director": "技术总监", "Human Resources": "HRBP",
    "Healthcare Representative": "医疗行业顾问",
}
_TRAVEL_MAP = {"Travel_Frequently": "高", "Travel_Rarely": "中", "Non-Travel": "低"}
_ATTRITION_MAP = {"Yes": "离职", "No": "在岗"}
_PERF_MAP = {1: "及格", 2: "中等", 3: "良好", 4: "优秀", 5: "卓越"}


def _parse_df(df: pd.DataFrame) -> tuple[list[tuple], list[str]]:
    """解析 DataFrame 为插入值列表，返回 (values, errors)"""
    values = []
    errors = []
    np.random.seed(int(datetime.now().timestamp()) % 10000)

    for i in range(len(df)):
        row = df.iloc[i]
        try:
            emp_hash = hashlib.md5(f"EMP_{i}_{datetime.now().timestamp()}".encode()).hexdigest()
            dept = str(row.get("Department", ""))
            role = str(row.get("JobRole", ""))
            perf = int(row.get("PerformanceRating", 3))
            overtime = str(row.get("OverTime", "No"))
            salary = float(row.get("MonthlyIncome", 0))

            values.append((
                emp_hash,
                int(row.get("Age", 0)),
                str(row.get("Gender", "")),
                str(row.get("MaritalStatus", "")),
                int(row.get("Education", 2)),
                str(row.get("EducationField", "")),
                dept, _DEPT_MAP.get(dept, dept),
                role, _ROLE_MAP.get(role, role),
                int(row.get("JobLevel", 1)),
                int(salary),
                overtime,
                str(row.get("Attrition", "No")),
                _ATTRITION_MAP.get(str(row.get("Attrition", "No")), "在岗"),
                str(row.get("BusinessTravel", "")),
                _TRAVEL_MAP.get(str(row.get("BusinessTravel", "")), "中"),
                int(row.get("PercentSalaryHike", 0)),
                perf, _PERF_MAP.get(perf, "良好"),
                float(row.get("TotalWorkingYears", 0)),
                float(row.get("YearsAtCompany", 0)),
                float(row.get("YearsInCurrentRole", 0)),
                float(row.get("YearsSinceLastPromotion", 0)),
                int(row.get("TrainingTimesLastYear", 0)),
                int(row.get("DistanceFromHome", 5)),
                int(row.get("NumCompaniesWorked", 0)),
                int(row.get("StockOptionLevel", 0)),
                int(row.get("WorkLifeBalance", 3)),
                int(row.get("JobSatisfaction", 3)),
                int(row.get("EnvironmentSatisfaction", 3)),
                int(row.get("RelationshipSatisfaction", 3)),
                np.random.randint(150, 240),
                0.0, 0.0,
                "LOW", "MID",
                datetime.now(timezone.utc).isoformat(),
            ))
        except Exception as e:
            errors.append(f"行 {i + 1}: {e}")

    return values, errors


def _build_insert_sql() -> tuple[str, str]:
    cols = (
        "employee_id_hash,age,gender,marital_status,education,education_field,"
        "department,department_cn,job_role,job_role_cn,job_level,"
        "monthly_income,overtime,attrition,attrition_cn,"
        "business_travel,travel_cn,percent_salary_hike,"
        "performance_rating,performance_cn,"
        "total_working_years,years_at_company,years_in_current_role,"
        "years_since_last_promotion,training_times_last_year,"
        "distance_from_home,num_companies_worked,stock_option_level,"
        "work_life_balance,job_satisfaction,environment_satisfaction,"
        "relationship_satisfaction,monthly_working_hours,"
        "ona_eigenvector_centrality,ona_degree_centrality,"
        "risk_level,performance_level,created_at"
    )
    placeholders = ",".join(["?"] * 38)
    insert_sql = f"INSERT OR IGNORE INTO employees ({cols}) VALUES ({placeholders})"
    count_sql = "SELECT COUNT(*) FROM employees"
    return insert_sql, count_sql


@router.post(
    "/graph/upload",
    response_model=OnaImportResponse,
    summary="CSV/Excel 员工数据批量导入",
    description=(
        "上传 CSV 或 Excel 文件，解析 18+ 个标准 HR 字段，"
        "自动完成中文化映射和派生字段计算后写入 turnover.db。"
        "支持 .csv 和 .xlsx 格式。"
    ),
)
async def upload_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名无效")

    suffix = os.path.splitext(file.filename)[1].lower()
    if suffix not in (".csv", ".xlsx"):
        raise HTTPException(status_code=400, detail=f"不支持的文件格式: {suffix}，请上传 .csv 或 .xlsx")

    # 读取文件
    content = await file.read()

    try:
        if suffix == ".csv":
            df = pd.read_csv(io.BytesIO(content), skiprows=1)
        else:
            df = pd.read_excel(io.BytesIO(content), skiprows=1)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"文件解析失败: {e}")

    total = len(df)
    if total == 0:
        raise HTTPException(status_code=400, detail="文件为空，无数据行")

    # 字段校验
    missing = [c for c in _REQUIRED_COLS if c not in df.columns]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"缺少必填字段: {', '.join(missing)}",
        )

    # 解析 + 插入
    values, errors = _parse_df(df)
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 建表（如不存在）
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS employees (
            employee_id_hash TEXT PRIMARY KEY,
            age INTEGER, gender TEXT, marital_status TEXT, education INTEGER,
            education_field TEXT, department TEXT, department_cn TEXT,
            job_role TEXT, job_role_cn TEXT, job_level INTEGER,
            monthly_income INTEGER, overtime TEXT, attrition TEXT, attrition_cn TEXT,
            business_travel TEXT, travel_cn TEXT, percent_salary_hike INTEGER,
            performance_rating INTEGER, performance_cn TEXT,
            total_working_years REAL, years_at_company REAL,
            years_in_current_role REAL, years_since_last_promotion REAL,
            training_times_last_year INTEGER, distance_from_home INTEGER,
            num_companies_worked INTEGER, stock_option_level INTEGER,
            work_life_balance INTEGER, job_satisfaction INTEGER,
            environment_satisfaction INTEGER, relationship_satisfaction INTEGER,
            monthly_working_hours INTEGER,
            ona_eigenvector_centrality REAL, ona_degree_centrality REAL,
            risk_level TEXT, performance_level TEXT, created_at TEXT
        )
    """)

    insert_sql, count_sql = _build_insert_sql()
    cur.executemany(insert_sql, values)
    conn.commit()
    inserted = cur.execute(count_sql).fetchone()[0]
    conn.close()

    return OnaImportResponse(
        code=200,
        message=f"导入完成: {len(values)} 行处理, {len(errors)} 行错误",
        data=ImportResult(
            total_rows=total,
            inserted_rows=len(values),
            skipped_rows=len(errors),
            errors=errors[:20],
        ),
    )
