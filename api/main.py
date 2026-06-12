"""
员工离职风险预测与管理平台 —— FastAPI 应用入口
"""

import traceback, sys
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
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


# =============================================================================
# Demo 路径全局异常兜底（第二道防线）
# 确保演示时任何未捕获异常不返回 500，而是返回含 Mock 数据的友好响应
# =============================================================================
@app.exception_handler(Exception)
async def demo_safe_fallback(request: Request, exc: Exception):
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    print(f"[DEMO_FALLBACK] {request.method} {request.url.path}: {exc}\n{tb}", file=sys.stderr)
    path = request.url.path

    # PDF 导出降级：返回简单 PDF
    if "/report/" in path:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        import io
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=20*mm, bottomMargin=15*mm)
        styles = getSampleStyleSheet()
        elements = [Paragraph("核心骨干离职风险留任建议书（降级版）", styles["Title"]),
                    Spacer(1, 10*mm),
                    Paragraph("系统遇临时错误，以下为预设参考数据。请稍后重试。", styles["Normal"]),
                    Spacer(1, 5*mm),
                    Paragraph(f"错误信息: {exc}", styles["Normal"])]
        doc.build(elements)
        buf.seek(0)
        from datetime import datetime
        return StreamingResponse(buf, media_type="application/pdf",
                                headers={"Content-Disposition": f'attachment; filename="fallback_report_{datetime.now().strftime("%Y%m%d")}.pdf"'})

    # ROI/诊断/悬停等 JSON 接口降级：返回 mock 默认值
    return JSONResponse(
        status_code=200,
        content={
            "code": 200,
            "message": "Demo fallback — service temporarily degraded",
            "trace_id": f"demo_fallback_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "data": None,
        },
    )


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
