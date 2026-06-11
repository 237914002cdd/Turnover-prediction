"""
员工离职风险预测与管理平台 —— ROI 引擎 & ONA 综合风险判定
================================================================
依据: Master PRD V4.0
  - 第三章 核心算法仓库与 KPI 财务测算模型
  - 第五章 PRD 规格 — 预警仪表盘排序公式
  - 第二章 特征相关性判定

核心功能:
  1. compute_risk_level()    — 根据离职概率 + ONA 中心度 → 红/橙/黄等级
  2. compute_roi_kpi()       — KPI 损益测算（严格对照员工 A 实例）
  3. compute_sort_score()    — 仪表盘排名分 = P(离职) × ONA 权重 × 绩效权重
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


# =============================================================================
# 风险等级定义
# =============================================================================
class RiskLevel(Enum):
    RED = "红色预警"
    ORANGE = "橙色预警"
    YELLOW = "黄色提示"


# =============================================================================
# 数据容器
# =============================================================================
@dataclass
class EmployeeRiskProfile:
    """单个员工的风险画像计算结果"""
    employee_id: str
    base_attrition_prob: float          # 基础离职概率 (0~1)
    ona_centrality: float               # ONA 网络中心度 (0~1)
    performance_weight: float            # 绩效权重 (0~1+)
    composite_score: float               # 综合风险分
    risk_level: RiskLevel                # 红/橙/黄等级
    top_shap_factors: list[tuple[str, float]] = None  # SHAP 归因因子


@dataclass
class ROICalculationResult:
    """单次 KPI 损益测算结果"""
    # --- 调薪前 ---
    pre_attrition_prob: float          # 调薪前离职概率 (0~1)
    pre_expected_cost: float           # 调薪前预期离职花费（元）
    # --- 调薪方案 ---
    current_salary: float              # 当前月薪（元）
    market_salary: float               # 外部市场中位薪资（元）
    new_salary: float                  # 调薪后月薪（元）
    raise_amount_per_month: float      # 每月涨薪额（元）
    # --- 调薪后 ---
    post_attrition_prob: float         # 调薪后离职概率 (0~1)
    post_expected_cost: float          # 调薪后预期离职花费（元）
    # --- 投入与结论 ---
    total_investment: float            # 企业总投入（元）= 涨薪额 × 12
    net_savings: float                 # 净节约金额（元）—— 决策判定值
    is_positive_roi: bool              # 投资回报率是否为正值
    recommendation: str                # 决策建议


# =============================================================================
# 1. 风险等级综合判定
# =============================================================================
def compute_risk_level(
    base_attrition_prob: float,
    ona_centrality: float = 0.0,
    performance_weight: float = 1.0,
    prob_threshold_red: float = 0.6,
    prob_threshold_orange: float = 0.3,
    centrality_boost_threshold: float = 0.7,
) -> tuple[RiskLevel, float]:
    """
    综合风险判定 + 排序分计算。

    算法逻辑 (PRD 第三章/第五章):
      composite_score = base_attrition_prob × (1 + ona_centrality × 2) × performance_weight

      解释:
        - ONA 中心度高(≥0.7) 的员工即使基础概率中等，也会因扩散效应被抬级。
        - 绩效权重 > 1.0 用于强调高绩效者的特级警报。
        - 最终排名分遵循 PRD 公式：排序分 = 离职概率 × ONA中心度权重 × 绩效权重

    Parameters
    ----------
    base_attrition_prob : float
        基础离职概率 (0~1)，来自随机森林/逻辑回归模型输出。
    ona_centrality : float
        ONA 网络中心度 (0~1)，由交互频次矩阵计算得出。
    performance_weight : float
        绩效权重。高绩效(≥4.0/5.0) 建议设为 1.2~1.5 以提升警报优先级。
    prob_threshold_red : float
        红色预警门槛（默认 0.6）
    prob_threshold_orange : float
        橙色预警门槛（默认 0.3）
    centrality_boost_threshold : float
        中心度放大生效阈值（默认 0.7）

    Returns
    -------
    tuple[RiskLevel, float]
        (风险等级, 综合排序分)
    """
    # 综合排序分 = 离职概率 × (1 + ONA中心度放大) × 绩效权重
    centrality_boost = 1.0 + ona_centrality * 2.0  # 中心度最高 3x 放大
    composite_score = base_attrition_prob * centrality_boost * performance_weight

    # ---- 等级判定 ----
    # 红色：基础概率高 或 基础概率中等但 ONA 中心度极高
    if base_attrition_prob >= prob_threshold_red:
        level = RiskLevel.RED
    elif base_attrition_prob >= prob_threshold_orange:
        # ONA 中心度 ≥ 0.7 时将橙色抬为红色
        if ona_centrality >= centrality_boost_threshold:
            level = RiskLevel.RED
        else:
            level = RiskLevel.ORANGE
    else:
        # 低概率但高中心度 → 仍黄色提示（不忽视潜在扩散源）
        level = RiskLevel.YELLOW

    return level, round(composite_score, 4)


# =============================================================================
# 2. KPI 财务损益测算（ROI 引擎）
# =============================================================================
def compute_roi_kpi(
    current_salary: float,
    market_salary: float,
    hire_cost: float,
    pre_attrition_prob: float,
    post_attrition_prob: float,
    raise_pct: float = 0.10,
) -> ROICalculationResult:
    """
    KPI 财务损益测算 —— 完全遵循 PRD 第三章公式和员工 A 实例。

    公式链 (PRD V4.0 第三章第一节):
      ① 预期离职花费(干预前) = P_pre × [ 招聘花费 + (市场薪资 - 当前月薪) × 12 ]
      ② 预期离职花费(干预后) = P_post × [ 招聘花费 + (市场薪资 - 调薪后月薪) × 12 ]
      ③ 投入资金 = 涨薪金额 × 12
      ④ 净节约金额 = ① - ② - ③

    验证: 使用 PRD 员工 A 实例数据
      当前月薪=13,000, 市场薪资=15,000, 招聘花费=1,000,
      P_pre=80%, P_post=20%, 涨薪10%
      → 净节约金额 = 2,520 元（精确匹配文档 Table 0）

    Parameters
    ----------
    current_salary : float
        员工当前月薪（元）。
    market_salary : float
        外部同职级市场中位月薪（元）。
    hire_cost : float
        岗位招聘替换花费（元，一次性）。
    pre_attrition_prob : float
        调薪前离职概率 (0~1)。
    post_attrition_prob : float
        调薪后离职概率 (0~1)。
    raise_pct : float
        建议调薪幅度，默认 10% (0.10)。

    Returns
    -------
    ROICalculationResult
        包含完整演算过程和决策建议的数据类。
    """
    # 调薪计算
    raise_amount = current_salary * raise_pct
    new_salary = current_salary + raise_amount

    # 薪资溢价（外部市场 - 当前/调薪后）
    pre_premium = max(0.0, market_salary - current_salary)
    post_premium = max(0.0, market_salary - new_salary)

    # ① 调薪前预期离职花费
    pre_expected = pre_attrition_prob * (hire_cost + pre_premium * 12)

    # ② 调薪后预期离职花费
    post_expected = post_attrition_prob * (hire_cost + post_premium * 12)

    # ③ 企业实际投入资金
    total_investment = raise_amount * 12

    # ④ 净节约金额（决策判定值）
    net_savings = pre_expected - post_expected - total_investment

    # ROI 判定
    is_positive = net_savings > 0
    if is_positive:
        recommendation = "⭐ 优选执行决策：该调薪方案净节约金额为正，建议 HRBP 立即执行调薪挽留方案。"
    else:
        recommendation = (
            "⚠ 需复审：当前调薪方案净节约为负或持平。建议：\n"
            "  (a) 提高调薪幅度重新测算；\n"
            "  (b) 考虑非财务手段（调岗/ONA 纽带沟通）；\n"
            "  (c) 确认员工是否已有不可控离职因素（家庭搬迁等）。"
        )

    return ROICalculationResult(
        pre_attrition_prob=pre_attrition_prob,
        pre_expected_cost=round(pre_expected, 2),
        current_salary=current_salary,
        market_salary=market_salary,
        new_salary=round(new_salary, 2),
        raise_amount_per_month=round(raise_amount, 2),
        post_attrition_prob=post_attrition_prob,
        post_expected_cost=round(post_expected, 2),
        total_investment=round(total_investment, 2),
        net_savings=round(net_savings, 2),
        is_positive_roi=is_positive,
        recommendation=recommendation,
    )


# =============================================================================
# 3. 员工 A 真实实例 — 精确验证函数
# =============================================================================
def employee_a_validation() -> ROICalculationResult:
    """
    精确复现 PRD 文档中员工 A 的 KPI 测算实例（Table 0）。

    PRD 原始数据:
      - 当前月薪: 13,000 元
      - 市场薪资: 15,000 元
      - 招聘花费: 1,000 元
      - 调薪前离职概率: 80%
      - 调薪幅度: 10% → 涨薪 1,300 元/月 → 新月薪 14,300 元
      - 调薪后离职概率降至: 20%
      - 预期调薪前花费: 20,000 元
      - 预期调薪后花费: 1,880 元
      - 投入资金: 15,600 元
      - 净节约金额: 2,520 元 ✅

    Returns
    -------
    ROICalculationResult
    """
    return compute_roi_kpi(
        current_salary=13000.0,
        market_salary=15000.0,
        hire_cost=1000.0,
        pre_attrition_prob=0.80,
        post_attrition_prob=0.20,
        raise_pct=0.10,
    )


# =============================================================================
# 4. 工具: 获取干预建议策略（Playbook 匹配）
# =============================================================================
def match_playbook_strategy(
    top_shap_factors: list[tuple[str, float]],
    risk_level: RiskLevel,
) -> list[str]:
    """
    根据 SHAP 归因因子匹配干预建议策略（PRD 第五章第二节）。

    策略匹配:
      - Monthly_Income / Salary_Increase_Pct 低 → 薪酬焦虑型
      - Tenure_Years 长 + Job_Level 未晋升  → 职业发展型
      - Overtime_Hours 超高 + Attendance_Anomaly 多 → 工作负荷异常型
      - ONA 中心度超高                     → ONA 组织网络纽带型

    Parameters
    ----------
    top_shap_factors : list[(str, float)]
        SHAP 重要性排名前 N 的 (特征名, SHAP 值) 列表。
    risk_level : RiskLevel
        当前风险等级。

    Returns
    -------
    list[str]
        建议行动项。
    """
    actions = []
    factor_names = {name for name, _ in top_shap_factors}

    if "Salary_Increase_Pct" in factor_names or "Monthly_Income" in factor_names:
        actions.append(
            "【薪酬焦虑型】建议执行: 薪酬核查谈话 → 输出同业同职级对标报表 "
            "→ 启动调薪审批流程。"
        )

    if "Tenure_Years" in factor_names and "Job_Level" not in factor_names:
        actions.append(
            "【职业发展型】建议执行: 推送内部轮岗机会列表 → 安排导师双向沟通 "
            "→ 讨论未来项目授权框架。"
        )

    if "Overtime_Hours" in factor_names:
        actions.append(
            "【工作负荷异常型(Burnout)】建议执行: 强制休假提醒 → 评估项目负荷 "
            "→ 跨组分流建议。"
        )

    if risk_level == RiskLevel.RED and any(
        "ONA" in name or "centrality" in name for name in factor_names
    ):
        actions.append(
            "【ONA 组织网络纽带型】建议执行: 高管非正式关怀谈话 → 组织核心归属感沟通 "
            "→ 制定留任保留方案(非财务手段优先)。"
        )

    if not actions:
        actions.append("定期跟踪观察，无需紧急干预。")

    return actions


# =============================================================================
# 示例：直接运行此文件时验证员工 A 的 ROI 测算
# =============================================================================
if __name__ == "__main__":
    print("=" * 64)
    print("  员工离职风险预测 · ROI 引擎验证")
    print("=" * 64)

    # ---- 验证 1: 员工 A 演算 ----
    print("\n▶ 员工 A 实例演算（精确复现 PRD Table 0）")
    result = employee_a_validation()
    print(f"  当前月薪:         {result.current_salary:>8,.0f} 元")
    print(f"  市场薪资:         {result.market_salary:>8,.0f} 元")
    print(f"  调薪方案:         涨薪 {result.raise_amount_per_month:>6,.0f} 元/月 → {result.new_salary:>8,.0f} 元")
    print(f"  调薪前预期离职花费: {result.pre_expected_cost:>10,.0f} 元")
    print(f"  调薪后预期离职花费: {result.post_expected_cost:>10,.0f} 元")
    print(f"  企业投入资金:      {result.total_investment:>10,.0f} 元")
    print(f"  ──────────────────────────────")
    print(f"  净节约金额:        {result.net_savings:>10,.0f} 元  ✅ 预期=2,520 元")
    assert abs(result.net_savings - 2520.0) < 0.01, f"验证失败: {result.net_savings} != 2520"
    print(f"  判定:              {result.recommendation}")
    print(f"  ROI 为正:          {result.is_positive_roi}")

    # ---- 验证 2: 风险等级判定 ----
    print("\n▶ 风险等级判定（ONA 影响）")
    test_cases = [
        ("低概率+低中心度", 0.25, 0.3),
        ("中等概率+高中心度 → 红色抬级", 0.35, 0.8),
        ("高概率+高中心度", 0.75, 0.9),
        ("低概率+高中心度→黄色预警", 0.20, 0.85),
    ]
    for label, prob, centrality in test_cases:
        level, score = compute_risk_level(prob, ona_centrality=centrality)
        print(f"  {label:<30s}  P={prob:.2f} C={centrality:.2f} → {level.value} (分={score:.3f})")

    # ---- 验证 3: SHAP 策略匹配 ----
    print("\n▶ Playbook 策略匹配示例")
    factors = [("Salary_Increase_Pct", -0.32), ("Overtime_Hours", 0.28)]
    actions = match_playbook_strategy(factors, RiskLevel.RED)
    for a in actions:
        print(f"  → {a}")

    print("\n✅ 所有验证通过！")
