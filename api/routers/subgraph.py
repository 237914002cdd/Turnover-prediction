"""
ONA 子图（Ego Network）—— FastAPI 路由
接口: GET /api/v1/ona/graph/subgraph?center_employee_id_hash=...&depth=2

从 turnover.db 动态查询，不 dump 全部 1470 节点
"""

from fastapi import APIRouter, HTTPException, status
from api.models.ona_models import (
    SubgraphResponse, SubgraphData, SubgraphNode, SubgraphEdge,
)
from api.services.db import get_neighbors
from api.services.interpretation import get_anchor_display_name

router = APIRouter(prefix="/api/v1/ona", tags=["ONA 拓扑交互"])


def _node_label(n: dict) -> str:
    anchor = get_anchor_display_name(n.get("employee_id_hash", ""))
    return anchor if anchor else n.get("job_role_cn", "未知")


@router.get(
    "/graph/subgraph",
    response_model=SubgraphResponse,
    summary="Ego Network 子图隔离查询（~10ms）",
)
async def get_subgraph(
    center_employee_id_hash: str,
    depth: int = 2,
):
    if not center_employee_id_hash or len(center_employee_id_hash) < 8:
        raise HTTPException(status_code=400, detail="center_employee_id_hash 长度不足或无效")

    nodes, edges = get_neighbors(center_employee_id_hash, min(depth, 3))

    node_models = []
    for n in nodes:
        ec = float(n.get("ona_eigenvector_centrality", 0))
        risk = n.get("risk_level", "LOW")
        fill = "#FF4D4F" if risk == "HIGH" else "#FA8C16" if risk == "MID" else "#5B8FF9"
        node_models.append(SubgraphNode(
            id=n["employee_id_hash"],
            label=_node_label(n),
            size=max(20, int(ec * 50)),
            style={"fill": fill, "stroke": fill, "lineWidth": 2},
            description=f"{n.get('department_cn','')} · 中心度{ec:.2f}",
        ))

    edge_models = [SubgraphEdge(**e) for e in edges]

    return SubgraphResponse(
        code=200, message="Success",
        data=SubgraphData(nodes=node_models, edges=edge_models, total=len(node_models)),
    )


@router.get(
    "/graph/topology",
    response_model=SubgraphResponse,
    summary="全局拓扑图（Top 100 Hub 节点）",
)
async def get_topology():
    """返回按 EC 降序的前 100 个节点及其关联边"""
    from api.services.db import get_top_hubs

    hubs = get_top_hubs(100)
    node_ids = {h["employee_id_hash"] for h in hubs}
    node_models = []
    edge_models = []

    for h in hubs:
        ec = float(h.get("ona_eigenvector_centrality", 0))
        risk = h.get("risk_level", "LOW")
        fill = "#FF4D4F" if risk == "HIGH" else "#FA8C16" if risk == "MID" else "#5B8FF9"
        node_models.append(SubgraphNode(
            id=h["employee_id_hash"],
            label=_node_label(h),
            size=max(20, int(ec * 50)),
            style={"fill": fill, "stroke": fill, "lineWidth": 2},
            description=f"{h.get('department_cn','')} · {h.get('performance_cn','')}",
        ))

    # 同部门之间生成边
    dept_groups = {}
    for h in hubs:
        d = h.get("department_cn", "")
        dept_groups.setdefault(d, []).append(h["employee_id_hash"])
    for dept, ids in dept_groups.items():
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                if j - i <= 3:  # 只连最近邻避免膨胀
                    edge_models.append(SubgraphEdge(source=ids[i], target=ids[j]))

    return SubgraphResponse(
        code=200, message="Success",
        data=SubgraphData(nodes=node_models, edges=edge_models, total=len(node_models)),
    )
