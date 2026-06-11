"""
ONA 悬停弹窗 —— Mock 数据服务

完全遵循用户提供的 JSON 协议规范，以文档中的"申鹏程"为例构建
"""

from datetime import datetime, timezone
from api.models.ona_models import (
    ONAHoverData, NodeInfo, RiskMetrics, SHAPFactor,
    CascadeEffect, ConnectedNode, PlaybookAction,
    RiskLevel,
)

_MOCK_SEQ = 0


def _next_trace_id() -> str:
    global _MOCK_SEQ
    _MOCK_SEQ += 1
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"ona_hover_tr_{today}_{_MOCK_SEQ:03d}"


def build_mock_hover_data(employee_id_hash: str) -> ONAHoverData:
    """
    构造 mock 悬停响应体。

    Args:
        employee_id_hash: 前端传入的节点 ID（MD5 脱敏工号）。

    Returns:
        ONAHoverData，若匹配"申鹏程"则返回文档精确数据，
        否则返回通用模拟数据。
    """
    # 申鹏程 — 文档中的核心网络枢纽（Hub）案例
    if employee_id_hash == "e10adc3949ba59abbe56e057f20f883e":
        return ONAHoverData(
            node_info=NodeInfo(
                employee_id_hash="e10adc3949ba59abbe56e057f20f883e",
                display_alias="员工-申鹏程 (脱敏标识)",
                department="技术研发部-架构组",
                job_level="P5",
                tenure_years=1.5,
                performance_score=4.5,
            ),
            risk_metrics=RiskMetrics(
                final_risk_level=RiskLevel.RED,
                base_turnover_probability=0.82,
                ona_centrality_score=0.96,
                organization_shock_index=0.98,
                total_replacement_cost_cny=25000.00,
            ),
            shap_risk_factors=[
                SHAPFactor(
                    factor_name="Salary_Increase_Pct",
                    factor_label="近一年薪资涨幅停滞",
                    shap_value=0.35,
                    current_value="0.0%",
                ),
                SHAPFactor(
                    factor_name="Overtime_Hours",
                    factor_label="月度加班时长超载",
                    shap_value=0.28,
                    current_value="64.5小时",
                ),
                SHAPFactor(
                    factor_name="YearsAtCompany",
                    factor_label="任现职年限面临晋升瓶颈",
                    shap_value=0.19,
                    current_value="1.5年",
                ),
            ],
            cascade_effect_prediction=CascadeEffect(
                direct_impact_nodes_count=3,
                total_downstream_risks_count=10,
                co_leaver_risk_multiplier=2.4,
                high_risk_connected_nodes=[
                    ConnectedNode(
                        employee_id_hash="c4ca4238a0b923820dcc509a6f75849b",
                        display_alias="核心研发-员工B",
                        interaction_frequency=142,
                        current_risk_level=RiskLevel.YELLOW,
                    ),
                    ConnectedNode(
                        employee_id_hash="c81e728d9d4c2f636f067f89cc14862c",
                        display_alias="产品经理-员工C",
                        interaction_frequency=98,
                        current_risk_level=RiskLevel.GREEN,
                    ),
                    ConnectedNode(
                        employee_id_hash="eccbc87e4b5ce2fe28308fd9f2a7baf3",
                        display_alias="测试骨干-员工D",
                        interaction_frequency=85,
                        current_risk_level=RiskLevel.YELLOW,
                    ),
                ],
            ),
            matched_playbook=PlaybookAction(
                strategy_type="ONA_NETWORK_TIE",
                strategy_title="ONA 组织网络纽带型干预剧本",
                action_items=[
                    "触发高管/架构组负责人非正式关怀谈话，肯定其隐藏的技术及组织纽带价值。",
                    "即刻发起核心员工归属感专项沟通，排查跨部门协作摩擦点。",
                    "评估其在非正式组织中的技术辐射能量，将其纳入下期官方导师（Mentor）资源池。",
                ],
            ),
        )

    # 通用 mock：低风险边缘节点
    return ONAHoverData(
        node_info=NodeInfo(
            employee_id_hash=employee_id_hash,
            display_alias=f"员工-{employee_id_hash[:8]} (脱敏标识)",
            department="通用部门",
            job_level=None,
            tenure_years=3.0,
            performance_score=3.5,
        ),
        risk_metrics=RiskMetrics(
            final_risk_level=RiskLevel.GREEN,
            base_turnover_probability=0.15,
            ona_centrality_score=0.12,
            organization_shock_index=0.15,
            total_replacement_cost_cny=8000.00,
        ),
        shap_risk_factors=[],
        cascade_effect_prediction=CascadeEffect(
            direct_impact_nodes_count=0,
            total_downstream_risks_count=1,
            co_leaver_risk_multiplier=1.0,
            high_risk_connected_nodes=[],
        ),
        matched_playbook=PlaybookAction(
            strategy_type="GENERAL",
            strategy_title="常规关注",
            action_items=["定期观察，无需紧急干预。"],
        ),
    )
