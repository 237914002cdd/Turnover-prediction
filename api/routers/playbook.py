"""
LLM 面谈 Playbook 生成 —— FastAPI 路由
接口: POST /api/v1/ona/playbook/generate

从 turnover.db 读取员工真实画像，动态构建剧本
"""

from fastapi import APIRouter, HTTPException, status
from api.models.ona_models import (
    PlaybookGenerateRequest, PlaybookGenerateResponse, PlaybookData,
)
from api.services.db import find_employee

router = APIRouter(prefix="/api/v1/ona", tags=["ONA 拓扑交互"])


def _generate_playbook(row: dict) -> str:
    ec = float(row.get("ona_eigenvector_centrality", 0))
    role = row.get("job_role_cn", "员工")
    dept = row.get("department_cn", "")
    salary = float(row.get("monthly_income", 0))
    hike = float(row.get("percent_salary_hike", 0))
    perf = row.get("performance_cn", "良好")
    overtime = row.get("overtime") == "Yes"
    risk = row.get("risk_level", "LOW")
    tenure = float(row.get("years_at_company", 0))

    centrality_desc = (
        "极高网络中心度，是该组织非正式沟通的核心枢纽。可能影响多名高绩效关联员工。"
        if ec >= 0.9 else
        f"中等网络中心度（{ec:.2f}），在团队内有一定非正式影响力。"
        if ec >= 0.4 else
        "网络依存度有限。"
    )

    return f"""## 👥 1. 面谈心理破冰策略

> 目标对象: {role} · {dept}
> 网络画像: {centrality_desc}

**开场 Q1 - 价值认可型**
> 你在团队中承担了重要的角色，尤其是在跨部门协作中发挥了关键的纽带作用。

**开场 Q2 - 压力排查型**
> 最近的工作节奏怎么样？有没有什么让你感到特别吃力的地方？

**开场 Q3 - 留任意向试探型**
> 如果让你对未来6个月做一个期待，你最先希望改变的是什么？

## 🔍 2. 跨部门协作排查清单

| 排查方向 | 问题 |
|----------|------|
| 资源协调 | 是否经常因为等待其他部门输入而影响交付？ |
| 技术决策参与感 | 关键决策时你的意见是否被充分听取？ |
| 沟通成本 | 跨部门沟通是否存在反复澄清的情况？ |
| 职业可见度 | 有没有获得足够的展示舞台？ |
| 团队归属感 | 除了工作交流，是否有自发性的团队互动？ |

{'极高网络中心度，需评估其对周边高绩效同事的影响。' if ec >= 0.9 else ''}

## 💼 3. 调薪底牌分步谈判话术

### Step 1：倾听与共情（前 5 分钟）
> 我们了解到你最近的工作强度比较大，薪资方面也有提升空间。今天想听听你的真实想法。

### Step 2：示证数据价值（中段 5-10 分钟）
> 公司已经针对薪酬竞争力做了评估，我们准备了一个调薪方案。

### Step 3：提出方案（后段 5 分钟）
> 根据绩效表现（{perf}），调薪方案在预算框架内处于靠前位置。

### Step 4：锁定留任（收尾 2 分钟）
> 如果你愿意留下来，我们会在一个月内逐步落实。一个月后我再约你聊一次。

## 📊 4. 风险监控与跟进计划

| 节点 | 动作 | 负责人 |
|------|------|--------|
| 第1-3天 | 完成面谈，记录诉求 | HRBP |
| 第7天 | 确认调薪审批进度 | HRBP |
| 第14天 | 跨部门协作改进启动 | 部门负责人 |
| 第21天 | 工作负荷评估 | HRBP |
| 第30天 | 复盘评估 | HRBP+负责人 |
"""


@router.post(
    "/playbook/generate",
    response_model=PlaybookGenerateResponse,
    summary="LLM 动态生成面谈干预剧本（Playbook）",
)
async def generate_playbook(body: PlaybookGenerateRequest):
    if not body.employee_id_hash or len(body.employee_id_hash) < 8:
        raise HTTPException(status_code=400, detail="invalid hash")

    row = find_employee(body.employee_id_hash)
    if row is None:
        raise HTTPException(status_code=404, detail="员工不存在")

    markdown = _generate_playbook(row)

    return PlaybookGenerateResponse(
        code=200, message="Success",
        data=PlaybookData(markdown_content=markdown),
    )
