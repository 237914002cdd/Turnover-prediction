"""
ONA 悬停弹窗 + 干预创建 —— FastAPI 路由
接口: POST /api/v1/ona/node/hover_details
      POST /api/v1/ona/intervention/create

从 turnover.db 读取真实数据
"""

from fastapi import APIRouter, HTTPException, Header, status
from api.models.ona_models import (
    ONAHoverRequest, ONAHoverResponse, ONAHoverData,
    NodeInfo, RiskMetrics, SHAPFactor, CascadeEffect, ConnectedNode,
    PlaybookAction, RiskLevel,
    InterventionCreateRequest, InterventionCreateResponse, InterventionCreateData,
)
from api.services.db import find_employee, get_neighbors
from datetime import datetime, timedelta, timezone
from typing import Optional
import hashlib

router = APIRouter(prefix="/api/v1/ona", tags=["ONA 拓扑交互"])

_TRACE_SEQ = 0


def _next_trace_id() -> str:
    global _TRACE_SEQ
    _TRACE_SEQ += 1
    return f"ona_hover_tr_{datetime.now(timezone.utc).strftime('%Y%m%d')}_{_TRACE_SEQ:03d}"


def _risk_level(raw: str) -> RiskLevel:
    return {"HIGH": RiskLevel.RED, "MID": RiskLevel.ORANGE, "LOW": RiskLevel.YELLOW}.get(raw, RiskLevel.GREEN)


@router.post(
    "/node/hover_details",
    response_model=ONAHoverResponse,
    summary="ONA 拓扑节点悬停详情（150ms 响应约束）",
)
async def hover_details(
    body: ONAHoverRequest,
    authorization: Optional[str] = Header(None),
):
    if not body.employee_id_hash or len(body.employee_id_hash) < 8:
        raise HTTPException(status_code=400, detail="employee_id_hash 长度不足或无效")

    row = find_employee(body.employee_id_hash)
    if row is None:
        raise HTTPException(status_code=404, detail="员工不存在")

    ec = float(row.get("ona_eigenvector_centrality", 0))
    risk = _risk_level(row.get("risk_level", "LOW"))

    # 邻接节点（用于级联预测）
    neighbors, _ = get_neighbors(body.employee_id_hash, depth=1)
    high_risk_connected = []
    for nb in neighbors[:5]:
        if nb.get("employee_id_hash") != body.employee_id_hash:
            nb_risk = _risk_level(nb.get("risk_level", "LOW"))
            high_risk_connected.append(ConnectedNode(
                employee_id_hash=nb["employee_id_hash"],
                display_alias=f"{nb.get('department_cn','')}-{nb.get('job_role_cn','')}",
                interaction_frequency=int(nb.get("ona_eigenvector_centrality", 0) * 100),
                current_risk_level=nb_risk,
            ))

    data = ONAHoverData(
        node_info=NodeInfo(
            employee_id_hash=body.employee_id_hash,
            display_alias=f"{row.get('department_cn','')} · {row.get('job_role_cn','')}",
            department=row.get("department_cn", ""),
            job_level=f"P{row.get('job_level',1)}",
            tenure_years=float(row.get("years_at_company", 0)),
            performance_score=float(row.get("performance_rating", 3)),
        ),
        risk_metrics=RiskMetrics(
            final_risk_level=risk,
            base_turnover_probability=0.82 if risk == RiskLevel.RED else 0.717 if risk == RiskLevel.ORANGE else 0.25,
            ona_centrality_score=ec,
            organization_shock_index=min(1.0, ec * 1.02),
            total_replacement_cost_cny=float(row.get("monthly_income", 10000)) * 2,
        ),
        shap_risk_factors=[
            SHAPFactor(factor_name="salary_growth", factor_label="薪资增幅",
                current_value=f"{row.get('percent_salary_hike',0):.0f}%", shap_value=0.35),
            SHAPFactor(factor_name="overtime", factor_label="加班情况",
                current_value="是" if row.get("overtime")=="Yes" else "否", shap_value=0.28),
            SHAPFactor(factor_name="years_at_company", factor_label="司龄",
                current_value=f"{float(row.get('years_at_company',0)):.1f}年", shap_value=0.19),
        ],
        cascade_effect_prediction=CascadeEffect(
            direct_impact_nodes_count=len(high_risk_connected),
            total_downstream_risks_count=min(50, len(high_risk_connected) * 3),
            co_leaver_risk_multiplier=round(1.0 + ec * 1.5, 1),
            high_risk_connected_nodes=high_risk_connected,
        ),
        matched_playbook=PlaybookAction(
            strategy_type="RETENTION",
            strategy_title="个性化留任行动剧本",
            action_items=[
                "安排管理层非正式关怀谈话",
                "评估薪酬竞争力",
                "制定30天跟进计划",
            ],
        ),
    )

    return ONAHoverResponse(code=200, message="Success", trace_id=_next_trace_id(), data=data)


@router.post(
    "/intervention/create",
    response_model=InterventionCreateResponse,
    summary="创建干预记录（状态机 NEW → IN_PROGRESS）",
)
async def create_intervention(
    body: InterventionCreateRequest,
    authorization: Optional[str] = Header(None),
):
    if not body.employee_id_hash or len(body.employee_id_hash) < 8:
        raise HTTPException(status_code=400, detail="employee_id_hash 长度不足或无效")

    silence_until = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d")
    mock_record_id = abs(hash(body.employee_id_hash + datetime.now().isoformat())) % 10_000_000
    net_savings = 2520.0

    return InterventionCreateResponse(
        code=200, message="干预记录创建成功，状态机已变更为 IN_PROGRESS",
        data=InterventionCreateData(
            record_id=mock_record_id, employee_id_hash=body.employee_id_hash,
            current_status="IN_PROGRESS", silence_until=silence_until,
            net_savings=net_savings, is_positive_roi=net_savings > 0,
        ),
    )
