"""
ROI 实时模拟测算 —— FastAPI 路由
接口: POST /api/v1/roi/simulate

从 turnover.db 读取员工的真实月薪和离职概率，执行物理公式
"""

import math
from fastapi import APIRouter, HTTPException, status
from api.models.ona_models import (
    RoiSimulationRequest, RoiSimulationResponse, RoiSimulationData,
)
from api.services.db import find_employee

router = APIRouter(prefix="/api/v1/roi", tags=["ROI 财务测算"])

_DEFAULT_SALARY = 10000.0
_DEFAULT_PROB = 0.35
_DEFAULT_MARKET = 15000.0


def _simulate_roi(
    base_prob: float,
    current_salary: float,
    market_salary: float,
    hire_cost: float,
    alpha: float,
    increase_pct: float,
) -> RoiSimulationData:
    X = increase_pct
    P_new = base_prob * math.exp(-alpha * X)
    new_salary = current_salary * (1 + X)

    pre_premium = max(0, market_salary - current_salary)
    post_premium = max(0, market_salary - new_salary)

    pre_expected = base_prob * (hire_cost + pre_premium * 12)
    post_expected = P_new * (hire_cost + post_premium * 12)
    invest_cost = (current_salary * X) * 12

    benefit = pre_expected - post_expected
    net_savings = benefit - invest_cost

    return RoiSimulationData(
        current_turnover_prob=round(base_prob, 4),
        proposed_turnover_prob=round(max(0, min(1, P_new)), 4),
        investment_cost=round(max(0, invest_cost), 2),
        benefit=round(max(0, benefit), 2),
        net_savings=round(net_savings, 2),
        is_preferred_decision=net_savings > 0,
    )


@router.post(
    "/simulate",
    response_model=RoiSimulationResponse,
    summary="ROI 实时模拟测算（防抖滑块驱动）",
)
async def simulate(body: RoiSimulationRequest):
    if not body.employee_id_hash or len(body.employee_id_hash) < 8:
        raise HTTPException(status_code=400, detail="invalid hash")

    row = find_employee(body.employee_id_hash)
    if row:
        salary = float(row.get("monthly_income", _DEFAULT_SALARY))
        risk = row.get("risk_level", "LOW")
        base_prob = 0.82 if risk == "HIGH" else 0.717 if risk == "MID" else 0.25
        alpha = 18.0 if risk == "HIGH" else 14.0 if risk == "MID" else 10.0
    else:
        salary = _DEFAULT_SALARY
        base_prob = _DEFAULT_PROB
        alpha = 10.0

    result = _simulate_roi(
        base_prob=base_prob, current_salary=salary,
        market_salary=max(salary * 1.15, _DEFAULT_MARKET),
        hire_cost=1000.0, alpha=alpha,
        increase_pct=body.salary_increase_pct,
    )

    return RoiSimulationResponse(code=200, message="Success", data=result)
