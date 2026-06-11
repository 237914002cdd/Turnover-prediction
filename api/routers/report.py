"""
PDF 报告导出 —— FastAPI 路由
接口: GET /api/v1/ona/report/{employee_id_hash}

生成《核心骨干离职风险留任建议书》PDF
"""

import io, math
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from api.services.db import find_employee
from api.services.interpretation import interpret_employee
from api.routers.roi_simulate import _simulate_roi

router = APIRouter(prefix="/api/v1/ona", tags=["ONA 报告导出"])

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable,
    )
    from reportlab.lib import colors
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


@router.get(
    "/report/{employee_id_hash}",
    summary="导出员工留任建议书 PDF",
    description="生成《核心骨干离职风险留任建议书》PDF，含驱动因子、ROI 测算、级联风险",
)
async def export_report(employee_id_hash: str):
    if not employee_id_hash or len(employee_id_hash) < 8:
        raise HTTPException(status_code=400, detail="invalid hash")

    if not HAS_REPORTLAB:
        raise HTTPException(status_code=500, detail="reportlab 未安装，无法生成 PDF")

    row = find_employee(employee_id_hash)
    if row is None:
        raise HTTPException(status_code=404, detail="员工不存在")

    alias, tag, narrative = interpret_employee(row)
    ec = float(row.get("ona_eigenvector_centrality", 0))
    salary = float(row.get("monthly_income", 0))
    market = max(salary * 1.15, 15000.0)
    risk = row.get("risk_level", "LOW")
    base_prob = 0.82 if risk == "HIGH" else 0.717 if risk == "MID" else 0.25
    alpha = 18.0 if risk == "HIGH" else 14.0 if risk == "MID" else 10.0

    # 12% 调薪 ROI 模拟
    roi = _simulate_roi(base_prob, salary, market, 1000.0, alpha, 0.12)
    dept = row.get("department_cn", "")
    role = row.get("job_role_cn", "")
    perf = row.get("performance_cn", "良好")

    # 构建 PDF
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=20*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("Title2", parent=styles["Heading1"], fontSize=18, spaceAfter=6*mm, textColor=HexColor("#1a1a2e"))
    h2_style = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=14, spaceBefore=8*mm, spaceAfter=4*mm, textColor=HexColor("#16213e"))
    normal = ParagraphStyle("Normal", parent=styles["Normal"], fontSize=10, leading=14, spaceAfter=3*mm)
    small = ParagraphStyle("Small", parent=styles["Normal"], fontSize=8, textColor=HexColor("#888888"))

    elements = []

    # 封面
    elements.append(Paragraph("核心骨干离职风险留任建议书", title_style))
    elements.append(HRFlowable(width="100%", color=HexColor("#FF4D4F")))
    elements.append(Spacer(1, 4*mm))
    elements.append(Paragraph(f"生成日期: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}", normal))
    elements.append(Paragraph(f"保密等级: 仅 HR 管理层查阅", normal))

    # 个人信息
    elements.append(Paragraph("一、员工基本画像", h2_style))
    info_data = [
        ["姓名", alias, "部门", dept],
        ["岗位", role, "绩效评级", perf],
        ["风险等级", risk, "ONA 组织核心影响力", f"{ec:.2f}"],
        ["管理标签", tag if tag else "—", "离职概率", f"{base_prob * 100:.1f}%"],
    ]
    t = Table(info_data, colWidths=[70, 130, 70, 130])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (0, -1), HexColor("#f5f5f5")),
        ("BACKGROUND", (2, 0), (2, -1), HexColor("#f5f5f5")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(t)

    # 管理洞察
    if narrative:
        elements.append(Paragraph(f"管理洞察: {narrative}", normal))

    # ROI 测算
    elements.append(Paragraph("二、调薪留任 ROI 沙盘推演（拟调薪 12%）", h2_style))
    roi_data = [
        ["指标", "调薪前", "调薪后"],
        ["月薪", f"¥{salary:,.0f}", f"¥{salary * 1.12:,.0f}"],
        ["离职概率", f"{base_prob * 100:.1f}%", f"{roi.proposed_turnover_prob * 100:.1f}%"],
        ["预期离职花费", f"¥{roi.current_turnover_prob * (1000 + max(0, market - salary) * 12):,.0f}",
         f"¥{roi.proposed_turnover_prob * (1000 + max(0, market - salary * 1.12) * 12):,.0f}"],
        ["企业投入", "—", f"¥{roi.investment_cost:,.0f}"],
        ["净节约金额", "—", f"¥{roi.net_savings:,.0f}"],
        ["决策判定", "—", "⭐ 优选执行" if roi.is_preferred_decision else "建议调和"],
    ]
    t2 = Table(roi_data, colWidths=[100, 120, 120])
    t2.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#1a1a2e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(t2)

    # 级联风险
    elements.append(Paragraph("三、组织网络连带风险", h2_style))
    cascade_text = f"该员工组织核心影响力为 {ec:.2f}。"
    if ec >= 0.8:
        cascade_text += " 属极高网络枢纽，离职可能引发多名高绩效关联员工连锁流失。建议优先干预。"
    elif ec >= 0.4:
        cascade_text += " 有一定网络影响力，建议密切观察。"
    else:
        cascade_text += " 网络依存度有限。"
    elements.append(Paragraph(cascade_text, normal))

    # 页脚
    elements.append(Spacer(1, 10*mm))
    elements.append(HRFlowable(width="100%", color=HexColor("#cccccc")))
    elements.append(Paragraph(
        "本报告由 员工离职风险预测与管理平台 自动生成 · 机密文件 · 请勿外传",
        small,
    ))

    doc.build(elements)
    buf.seek(0)

    filename = f"retention_report_{alias}_{datetime.now().strftime('%Y%m%d')}.pdf"
    # ASCII-only filename for latin-1 header compatibility
    safe_name = filename.encode("ascii", "replace").decode("ascii")
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}"'},
    )
