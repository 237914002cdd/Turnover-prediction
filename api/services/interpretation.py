"""
业务翻译层（Interpretation Layer）
将数据库 raw 数据注入管理语义标签和洞察叙事
"""

_LIXIA_HASH = "57b8594cec78434525901c921c70522f"
_SHEN_HASH = "e48501815547b9698f09b81f3cca90de"

# ── 锚点名册 ──
_ANCHOR_REGISTRY = {
    _LIXIA_HASH: {
        "display_alias": "李夏",
        "management_tag": "核心高危高产钻石",
        "insight_narrative": (
            "高绩效核心骨干，当前主动离职概率极高（危险期）。"
            "核心驱动因子为[长期加班]与[晋升停滞]，"
            "建议立即启动沙盘调薪与大厂管理关怀干预。"
        ),
    },
    _SHEN_HASH: {
        "display_alias": "申鹏程",
        "management_tag": "隐形组织章鱼 / 高负载错配",
        "insight_narrative": (
            "该员工处于核心业务协同网络的绝对中枢，"
            "特征向量中心度（EC）高达0.96。承担了极高的非正式沟通与救火成本，"
            "但职级薪酬显著低于其组织贡献度。离职将引发协同网络级联爆仓。"
        ),
    },
}


def interpret_employee(row: dict) -> tuple[str, str, str]:
    """
    对数据库行应用业务翻译层，返回 (display_alias, management_tag, insight_narrative)

    优先级:
      1. 锚点名册（李夏/申鹏程）
      2. 通用规则：风险+绩效 / EC+薪资
      3. 兜底：岗位名
    """
    emp_hash = row.get("employee_id_hash", "")

    # 1. 锚点匹配
    if emp_hash in _ANCHOR_REGISTRY:
        anchor = _ANCHOR_REGISTRY[emp_hash]
        return anchor["display_alias"], anchor["management_tag"], anchor["insight_narrative"]

    # 2. 通用规则
    risk = row.get("risk_level", "LOW")
    perf = row.get("performance_level", "MID")
    ec = float(row.get("ona_eigenvector_centrality", 0))
    salary = float(row.get("monthly_income", 0))
    role_cn = row.get("job_role_cn", "员工")
    dept_cn = row.get("department_cn", "")
    default_name = f"{dept_cn} · {role_cn}" if dept_cn else role_cn

    if risk == "HIGH" and perf == "HIGH":
        return default_name, "核心高危钻石", (
            "高绩效核心骨干，当前离职概率较高。建议优先启动干预流程。"
        )

    if ec > 0.8 and salary < 15000:
        return default_name, "高负载组织章鱼", (
            f"该员工ONA中心度高达{ec:.2f}，承担大量非正式协调工作，"
            "但薪资低于15000元，存在高负载低回报的错配风险。"
        )

    # 3. 兜底
    return default_name, "", ""


def get_anchor_display_name(employee_id_hash: str) -> str:
    """快速获取锚点显示名（用于拓扑图节点）"""
    if employee_id_hash in _ANCHOR_REGISTRY:
        return _ANCHOR_REGISTRY[employee_id_hash]["display_alias"]
    return None  # 调用方决定 fallback
