"""
ONA 悬停弹窗 API —— Pydantic 数据模型
完全遵循 Master PRD V4.0 及 JSON 交互协议规范
"""

from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# =============================================================================
# 枚举
# =============================================================================
class RiskLevel(str, Enum):
    RED = "RED"
    ORANGE = "ORANGE"
    YELLOW = "YELLOW"
    GREEN = "GREEN"


class NodeStatus(str, Enum):
    """节点的组织震荡指数状态"""
    CRITICAL = "CRITICAL"
    ELEVATED = "ELEVATED"
    NORMAL = "NORMAL"


# =============================================================================
# Request
# =============================================================================
class ONAHoverRequest(BaseModel):
    """悬停详情请求体"""
    employee_id_hash: str = Field(
        ..., description="前端悬停节点对应的脱敏员工 ID (MD5)"
    )
    timestamp: Optional[datetime] = Field(
        default=None, description="悬停发生时刻，用于链路追踪"
    )


# =============================================================================
# Response — 嵌套模型
# =============================================================================
class NodeInfo(BaseModel):
    """基础节点属性"""
    employee_id_hash: str = Field(
        ..., description="脱敏工号（MD5）"
    )
    display_alias: str = Field(
        ..., description="前端脱敏显示标识（如'员工-申鹏程 (脱敏标识)'）"
    )
    department: Optional[str] = Field(None, description="部门-组")
    job_level: Optional[str] = Field(None, description="职级")
    tenure_years: Optional[float] = Field(None, description="司龄（年）")
    performance_score: Optional[float] = Field(None, ge=0, le=5, description="最近绩效评分")


class RiskMetrics(BaseModel):
    """风险度量核心"""
    final_risk_level: RiskLevel = Field(..., description="综合风险等级（红/橙/黄/绿）")
    base_turnover_probability: float = Field(
        ..., ge=0, le=1, description="基础离职概率（模型输出，0~1）"
    )
    ona_centrality_score: float = Field(
        ..., ge=0, le=1, description="ONA 网络中心度（0~1）"
    )
    organization_shock_index: float = Field(
        ..., ge=0, le=1,
        description="组织震荡指数：该节点在整体网络中的枢纽百分位，越高表示一旦离职影响范围越广"
    )
    total_replacement_cost_cny: float = Field(
        ..., ge=0,
        description="个体替换成本：招聘花费 + 薪资溢价×12 + 隐性知识流失折算"
    )


class SHAPFactor(BaseModel):
    """单个 SHAP 归因因子"""
    factor_name: str = Field(..., description="特征技术名，如 Salary_Increase_Pct")
    factor_label: str = Field(..., description="前端展示标签，如'近一年薪资涨幅停滞'")
    shap_value: float = Field(..., description="SHAP 贡献绝对值，越大影响越强")
    current_value: str = Field(..., description="该特征当前值（带单位），如'0.0%' / '64.5小时'")


class ConnectedNode(BaseModel):
    """紧密关联的邻接节点"""
    employee_id_hash: str
    display_alias: str
    interaction_frequency: int = Field(..., ge=0, description="月度交互频次")
    current_risk_level: RiskLevel


class CascadeEffect(BaseModel):
    """多米诺级联流失预测"""
    direct_impact_nodes_count: int = Field(
        ..., ge=0, description="该节点若离职，一阶直接影响的员工数"
    )
    total_downstream_risks_count: int = Field(
        ..., ge=0, description="全链下游（一阶+二阶）潜在受影响人数"
    )
    co_leaver_risk_multiplier: float = Field(
        ..., ge=1.0,
        description="连带流失风险倍率：该节点离职将放大周围高绩效员工离职概率的倍率"
    )
    high_risk_connected_nodes: list[ConnectedNode] = Field(
        default_factory=list, description="紧密关联的高价值节点列表"
    )


class PlaybookAction(BaseModel):
    """干预剧本"""
    strategy_type: str = Field(
        ..., description="策略类型枚举：SALARY_ANXIETY / CAREER_DEVELOPMENT / BURNOUT / ONA_NETWORK_TIE"
    )
    strategy_title: str = Field(..., description="剧本标题，如'ONA 组织网络纽带型干预剧本'")
    action_items: list[str] = Field(
        ..., description="结构化行动项列表，供 HRBP 直接执行"
    )


class ONAHoverData(BaseModel):
    """悬停弹窗响应体"""
    node_info: NodeInfo
    risk_metrics: RiskMetrics
    shap_risk_factors: list[SHAPFactor] = Field(
        ..., description="SHAP 归因因子降序列表。PRD 要求：红/橙预警必须输出 ≥ 2 个显性指标"
    )
    cascade_effect_prediction: CascadeEffect
    matched_playbook: PlaybookAction


class ONAHoverResponse(BaseModel):
    """标准 API 响应"""
    code: int = Field(200, description="业务状态码；200=正常, 400=参数异常, 404=员工不存在")
    message: str = "Success"
    trace_id: str = Field(
        ..., description="链路追踪 ID 格式: ona_hover_tr_YYYYMMDD_序号"
    )
    data: Optional[ONAHoverData] = None


# =============================================================================
# 干预创建
# =============================================================================
class InterventionCreateRequest(BaseModel):
    """创建干预记录请求"""
    employee_id_hash: str = Field(..., description="待干预员工的脱敏 ID")
    proposed_salary_increase: float = Field(
        ..., ge=0, le=1, description="拟调薪幅度（小数），如 0.12 代表 12%"
    )


class InterventionCreateData(BaseModel):
    """创建结果"""
    record_id: int
    employee_id_hash: str
    current_status: str = "IN_PROGRESS"
    silence_until: str
    net_savings: Optional[float] = None
    is_positive_roi: Optional[bool] = None


class InterventionCreateResponse(BaseModel):
    """干预创建响应"""
    code: int = 200
    message: str = "Success"
    data: Optional[InterventionCreateData] = None


# =============================================================================
# ROI 实时重算
# =============================================================================
class RoiSimulationRequest(BaseModel):
    """ROI 模拟测算请求"""
    employee_id_hash: str = Field(..., description="员工脱敏 ID")
    salary_increase_pct: float = Field(
        ..., ge=0.0, le=0.3, description="拟调薪幅度 (0.0~0.3，如 0.12 代表 12%)"
    )


class RoiSimulationData(BaseModel):
    """ROI 模拟计算结果"""
    current_turnover_prob: float = Field(..., ge=0, le=1, description="当前离职概率")
    proposed_turnover_prob: float = Field(..., ge=0, le=1, description="调薪后离职概率")
    investment_cost: float = Field(..., ge=0, description="企业即期投入（元）")
    benefit: float = Field(..., ge=0, description="预期流失挽回收益（元）")
    net_savings: float = Field(..., description="净节约金额（元）；正=盈利，负=亏损")
    is_preferred_decision: bool = Field(..., description="是否为优选决策（Net Savings > 0）")


class RoiSimulationResponse(BaseModel):
    """ROI 模拟测算响应"""
    code: int = 200
    message: str = "Success"
    data: RoiSimulationData


# =============================================================================
# LLM Playbook 剧本生成
# =============================================================================
class PlaybookGenerateRequest(BaseModel):
    """Playbook 生成请求"""
    employee_id_hash: str = Field(..., description="员工脱敏 ID")


class PlaybookData(BaseModel):
    """Playbook 数据"""
    markdown_content: str = Field(..., description="完整的 Markdown 格式面谈指南")


class PlaybookGenerateResponse(BaseModel):
    """Playbook 生成响应"""
    code: int = 200
    message: str = "Success"
    data: PlaybookData


# =============================================================================
# 子图（Ego Network）查询
# =============================================================================
class SubgraphRequest(BaseModel):
    """子图查询请求"""
    center_employee_id_hash: str = Field(..., description="中心节点脱敏 ID")
    depth: int = Field(default=2, ge=1, le=3, description="子图深度（1=一阶，2=二阶，最大3）")


class SubgraphNode(BaseModel):
    """子图节点"""
    id: str
    label: str
    size: Optional[int] = 28
    style: Optional[dict] = None
    description: Optional[str] = None


class SubgraphEdge(BaseModel):
    """子图边"""
    source: str
    target: str


class SubgraphData(BaseModel):
    """子图数据"""
    nodes: list[SubgraphNode]
    edges: list[SubgraphEdge]
    total: int = Field(..., description="子图总节点数")


class SubgraphResponse(BaseModel):
    """子图响应"""
    code: int = 200
    message: str = "Success"
    data: SubgraphData


# =============================================================================
# 39 字段员工档案 + 归因诊断
# =============================================================================
class EmployeeExtendedProfile(BaseModel):
    """39 字段宽表映射的员工完整档案（用于诊断页展示）"""
    employee_id_hash: str
    display_alias: str
    # == 个人属性 ==
    age: int = Field(..., ge=18, le=100, description="年龄")
    gender: str = Field(..., pattern="^(男|女)$", description="性别")
    marital_status: str = Field(..., pattern="^(已婚|未婚)$", description="婚姻状况")
    education: str = Field(..., pattern="^(大专|本科|硕士研究生|博士研究生)$", description="最高学历")
    major: Optional[str] = Field(None, description="所学专业")
    # == 工龄职级 ==
    working_years: float = Field(..., ge=0, le=70, description="总工龄（年）")
    company_age: float = Field(..., ge=0, le=70, description="本公司工龄（年）")
    current_position_years: float = Field(..., ge=0, le=70, description="现职年限（年）")
    job_level: Optional[str] = Field(None, description="职级，如 P7")
    department: Optional[str] = Field(None, description="部门")
    # == 薪酬 ==
    monthly_salary: float = Field(..., ge=0, description="月薪（元）")
    salary_growth_pct: float = Field(..., ge=-1, le=10, description="薪资增幅（如 0.03=3%）")

    # == 考勤行为 ==
    travel_frequency: str = Field(..., pattern="^(高|中|低)$", description="出差频率")
    overtime_flag: bool = Field(..., description="是否经常加班（是=True）")
    monthly_working_hours: int = Field(..., ge=0, le=744, description="月平均工作时长（小时）")
    attendance_anomaly_count: int = Field(..., ge=0, le=100, description="上月考勤异常次数")
    attendance_anomaly_change: float = Field(..., ge=-10, le=10, description="上月考勤时长变化值（如-0.10=-10%）")
    leave_days: float = Field(..., ge=0, description="上月考勤请假天数")
    # == 绩效项目 ==
    performance_score: float = Field(..., ge=0, le=5, description="绩效考核得分")
    project_count: int = Field(..., ge=0, le=100, description="参与重大项目数量")
    promotion_count: int = Field(..., ge=0, le=50, description="晋升次数")
    training_hours: float = Field(..., ge=0, description="培训时长（小时）")
    # == 环境 ==
    work_satisfaction: int = Field(..., ge=1, le=5, description="工作满意度（1-5）")
    relationship_satisfaction: int = Field(..., ge=1, le=5, description="同事关系满意度（1-5）")
    environment_satisfaction: int = Field(..., ge=1, le=5, description="工作环境满意度（1-5）")
    # == ONA ==
    ona_centrality: float = Field(..., ge=0, le=1, description="ONA 网络中心度")
    # == 结果 ==
    total_turnover_prob: float = Field(..., ge=0, le=1, description="综合离职概率")
    risk_level: RiskLevel


class AttributionFactor(BaseModel):
    """单条归因因子"""
    factor_name: str
    factor_label: str
    current_value: str
    coefficient: float = Field(..., description="相关系数/权重")
    prob_contribution: float = Field(..., description="离职概率贡献值")
    adjusted_value: Optional[str] = Field(None, description="调整后的指标值（前端滑块联动后填充）")
    adjusted_prob: Optional[float] = Field(None, description="调整后的离职概率值")
    delta: Optional[float] = Field(None, description="变化值=调整后概率-原始概率贡献")


class DiagnosticRequest(BaseModel):
    """诊断请求"""
    employee_id_hash: str


class DiagnosticData(BaseModel):
    """诊断响应体"""
    employee_info: EmployeeExtendedProfile
    attribution_factors: list[AttributionFactor]


class DiagnosticResponse(BaseModel):
    """诊断响应"""
    code: int = 200
    message: str = "Success"
    data: DiagnosticData
