"""
员工诊断与归因矩阵 —— FastAPI 路由
接口: GET /api/v1/employee/diagnostic/{employee_id_hash}

从 turnover.db 读取真实员工数据，动态拼装诊断结果。
"""

from fastapi import APIRouter, HTTPException, status
from api.models.ona_models import (
    DiagnosticResponse, DiagnosticData, EmployeeExtendedProfile,
    AttributionFactor, RiskLevel,
)
from api.services.db import find_employee
import numpy as np

router = APIRouter(prefix="/api/v1/employee", tags=["员工诊断"])


_PERFORMANCE_MAP = {1: "及格", 2: "中等", 3: "良好", 4: "优秀", 5: "卓越"}
_TRAVEL_MAP = {"高": "高", "中": "中", "低": "低"}


def _row_to_profile(row: dict) -> EmployeeExtendedProfile:
    """数据库行 → Pydantic EmployeeExtendedProfile"""
    risk = RiskLevel.RED if row.get("risk_level") == "HIGH" else \
           RiskLevel.ORANGE if row.get("risk_level") == "MID" else \
           RiskLevel.YELLOW

    return EmployeeExtendedProfile(
        employee_id_hash=row.get("employee_id_hash", ""),
        display_alias=f"员工-{row.get('job_role_cn', '未知')}",
        age=row.get("age", 0),
        gender="男" if row.get("gender") == "Male" else "女",
        marital_status="已婚" if row.get("marital_status") == "Married" else "未婚",
        education={1:"大专",2:"本科",3:"硕士研究生",4:"博士研究生",5:"博士研究生"}.get(row.get("education", 2), "本科"),
        major=row.get("education_field", ""),
        working_years=float(row.get("total_working_years", 0)),
        company_age=float(row.get("years_at_company", 0)),
        current_position_years=float(row.get("years_in_current_role", 0)),
        job_level=f"P{row.get('job_level', 1)}",
        department=row.get("department_cn", "通用部门"),
        monthly_salary=float(row.get("monthly_income", 0)),
        salary_growth_pct=float(row.get("percent_salary_hike", 0)) / 100.0,
        travel_frequency=row.get("travel_cn", "中"),
        overtime_flag=row.get("overtime") == "Yes",
        monthly_working_hours=row.get("monthly_working_hours", 160),
        attendance_anomaly_count=0,
        attendance_anomaly_change=0.0,
        leave_days=0.0,
        performance_score=float(row.get("performance_rating", 3)),
        project_count=0,
        promotion_count=int(row.get("num_companies_worked", 0)),
        training_hours=float(row.get("training_times_last_year", 0)) * 8,
        work_satisfaction=int(row.get("job_satisfaction", 3)),
        relationship_satisfaction=int(row.get("relationship_satisfaction", 3)),
        environment_satisfaction=int(row.get("environment_satisfaction", 3)),
        ona_centrality=float(row.get("ona_eigenvector_centrality", 0)),
        total_turnover_prob=0.82 if row.get("risk_level") == "HIGH" else
                           0.717 if row.get("risk_level") == "MID" else 0.25,
        risk_level=risk,
    )


def _compute_attribution(row: dict) -> list[AttributionFactor]:
    """从数据库行生成归因因子（模拟 SHAP 值）"""
    ec = float(row.get("ona_eigenvector_centrality", 0))
    salary = float(row.get("monthly_income", 10000))
    pct_hike = float(row.get("percent_salary_hike", 0))
    perf = float(row.get("performance_rating", 3))
    overtime = row.get("overtime") == "Yes"
    tenure = float(row.get("years_at_company", 0))
    role_years = float(row.get("years_in_current_role", 0))

    factors = [
        AttributionFactor(factor_name="salary_growth", factor_label="薪资增幅",
            current_value=f"{pct_hike:.0f}%", coefficient=0.198,
            prob_contribution=0.163),
        AttributionFactor(factor_name="tenure_years", factor_label="任现职年限",
            current_value=f"{role_years:.0f}年", coefficient=0.177,
            prob_contribution=0.141),
        AttributionFactor(factor_name="overtime_hours", factor_label="月度加班超载",
            current_value=f"{'是' if overtime else '否'}", coefficient=0.165,
            prob_contribution=0.130),
        AttributionFactor(factor_name="ona_centrality", factor_label="ONA 网络中心度",
            current_value=f"{ec:.2f}", coefficient=0.152,
            prob_contribution=0.120),
        AttributionFactor(factor_name="training_hours", factor_label="培训时长",
            current_value=f"{int(row.get('training_times_last_year',0))*8}h", coefficient=-0.138,
            prob_contribution=0.108),
        AttributionFactor(factor_name="work_satisfaction", factor_label="工作满意度",
            current_value=f"{int(row.get('job_satisfaction',3))}/5", coefficient=0.125,
            prob_contribution=0.096),
        AttributionFactor(factor_name="perf_score", factor_label="绩效评分",
            current_value=f"{perf:.0f}/5", coefficient=0.112,
            prob_contribution=0.085),
        AttributionFactor(factor_name="leave_days", factor_label="请假天数",
            current_value="--", coefficient=0.098,
            prob_contribution=0.074),
    ]
    return sorted(factors, key=lambda f: f.prob_contribution, reverse=True)


@router.get(
    "/diagnostic/{employee_id_hash}",
    response_model=DiagnosticResponse,
    summary="员工诊断与归因矩阵",
)
async def get_diagnostic(employee_id_hash: str):
    if not employee_id_hash or len(employee_id_hash) < 8:
        raise HTTPException(status_code=400, detail="无效 ID")

    row = find_employee(employee_id_hash)
    if row is None:
        raise HTTPException(status_code=404, detail="员工不存在")

    profile = _row_to_profile(row)
    factors = _compute_attribution(row)

    return DiagnosticResponse(
        code=200, message="Success",
        data=DiagnosticData(employee_info=profile, attribution_factors=factors),
    )
