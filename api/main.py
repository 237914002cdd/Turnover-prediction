"""
员工离职风险预测与管理平台 —— FastAPI 应用入口
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import ona_hover, roi_simulate, playbook, subgraph, diagnostic, ona_import, report

app = FastAPI(
    title="员工离职风险预测与管理平台 API",
    description="Master PRD V4.0 — ROI 留任决策引擎 + ONA 拓扑交互",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ona_hover.router)
app.include_router(roi_simulate.router)
app.include_router(playbook.router)
app.include_router(subgraph.router)
app.include_router(diagnostic.router)
app.include_router(ona_import.router)
app.include_router(report.router)


@app.get("/health", tags=["系统"])
async def health_check():
    return {
        "status": "ok",
        "service": "turnover-prediction-api",
        "version": "0.2.0",
    }


@app.get("/", tags=["系统"])
async def root():
    return {
        "service": "员工离职风险预测与管理平台 API",
        "version": "0.3.0",
        "endpoints": [
            "GET  /health",
            "POST /api/v1/ona/node/hover_details",
            "POST /api/v1/ona/intervention/create",
            "POST /api/v1/roi/simulate",
            "POST /api/v1/ona/playbook/generate",
            "GET  /api/v1/ona/graph/subgraph",
            "GET  /api/v1/ona/graph/topology",
            "GET  /api/v1/employee/diagnostic/{id}",
            "POST /api/v1/ona/graph/upload",
            "GET  /api/v1/ona/report/{id}",
        ],
    }
