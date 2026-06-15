# 产品需求规格说明书 · PRD v0.3.0

**文档状态**: v0.3.0 · MVP 闭环版 · 2026-06-12  
**版本目标**: 完成核心 MVP 闭环：数据导入 → ONA 诊断 → SHAP 归因 → ROI 沙盘 → PDF 导出  
**研发团队**: 前端（React + Vite + AntV G6）+ 后端（FastAPI + SQLite + SHAP）  
**对标基线**: Workday Peakon / Visier / Glint / Culture Amp 差异化（详见 competitive_analysis.md）

---

## 1. Product Overview & Scope

### 1.1 版本定位

v0.3.0 是离职风险预测平台的 **MVP 闭环版本**，覆盖从数据导入到干预决策的端到端流程。这不是一个演示原型——它是一个可独立部署、包含完整数据管道和交互逻辑的生产级产品。

### 1.2 版本边界

| 范围 | Included | Excluded |
|------|----------|----------|
| 数据接入 | CSV/Excel 手动导入 | 实时 HRIS/飞书/钉钉 API 集成（NEXT） |
| 风险模型 | 基于 SHAP 的 Logistic Regression + ONA Eigenvector Centrality | 深层时序模型 + 知识图谱（v1.0） |
| 用户认证 | 无（演示模式直连） | 基于 OAuth2 的 RBAC 认证（v1.0） |
| 部署 | 单机 Docker | Kubernetes 集群 + HA 架构（v1.0） |
| 语言 | 中文 UI + 中英双语术语 | 多语言 i18n |

### 1.3 系统架构总览

```
┌─────────────┐    ┌───────────────┐    ┌──────────────┐
│  前端 (Vite) │───▶│  后端 (FastAPI) │───▶│   SQLite     │
│  AntV G6    │    │  SHAP Engine  │    │  turnovr.db  │
│  React 18   │    │  Report Lab   │    │  (1,470 rec) │
└─────────────┘    └───────────────┘    └──────────────┘
       │                    │
       │                    ▼
       │            ┌──────────────┐
       └───────────▶│  PDF Export   │
                    │  (ReportLab)  │
                    └──────────────┘
```

---

## 2. Feature List & Details

### 2.1 F1: ONA Focus Engine (拓扑图谱焦点模式)

**ID**: F-ONA-FOCUS  
**优先级**: P0  
**状态**: ✅ 已实现  

#### 2.1.1 功能描述

在全局 ONA 拓扑图谱中，当用户选中或悬停某个节点时，引擎以该节点为中心构建 **Ego Network（自我中心网络）**，将其直接相连的邻居节点高亮显示，非关联节点透明度降低。焦点模式默认高亮 SHEN_HASH（申鹏程）的一度邻居。

#### 2.1.2 交互流程

```
用户触发焦点 → 后端 /subgraph 返回中心节点 + 一度/二度邻居 →
前端 G6 Graph 更新：聚焦节点放大(30%)、一度邻居保留 opacity=1.0、
二度邻居 opacity=0.6、其余节点 opacity=0.1 →
右上角控制面板显示焦点标签 ("聚焦: 申鹏程")
```

#### 2.1.3 验收标准（Acceptance Criteria）

| # | 标准 | 指标 | 验证方法 |
|---|------|------|---------|
| AC1 | 初始加载默认聚焦 SHEN_HASH 一度邻居 | 12 个邻居节点高亮 | 页面加载后截图比对 |
| AC2 | 点击任意节点切换焦点 | 新节点及其邻居重绘 ≤ 100ms | Chrome DevTools Performance |
| AC3 | 非目标子图透明度降至 0.1 | CSS opacity 属性为 0.1 | 检查元素 computed style |
| AC4 | AntV G6/WebGL 在 1000+ 节点下交互帧率 | ≥ 60fps | Chrome DevTools FPS meter |
| AC5 | MouseLeave 拓扑图不自动退出焦点模式 | 焦点节点样式无变化 | 鼠标移出画布后截图 |
| AC6 | "聚焦申鹏程"快捷按钮一键复位 | 回到默认焦点状态 | 点击按钮验证 |

#### 2.1.4 数据契约（前端 ↔ 后端）

**请求**: `POST /api/v1/ona/graph/subgraph`
```json
{
  "center_employee_id_hash": "e48501815547b9698f09b81f3cca90de",
  "depth": 1
}
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "nodes": [
      {
        "id": "e48501...",
        "label": "申鹏程",
        "size": 48,
        "style": { "fill": "#f5222d", "stroke": "#ff4d4f" },
        "description": "P5 · 产研中心"
      }
    ],
    "edges": [{ "source": "e48501...", "target": "0031de..." }],
    "total": 13
  }
}
```

> 参考模型: `SubgraphResponse` / `SubgraphData` / `SubgraphNode` / `SubgraphEdge` (ona_models.py:223-255)

---

### 2.2 F2: SHAP Attribution Panel (局部白盒归因面板)

**ID**: F-SHAP-PANEL  
**优先级**: P0  
**状态**: ✅ 已实现  

#### 2.2.1 功能描述

对每位高危员工，计算其个人离职概率的 8 项核心驱动因子，按 SHAP 贡献值降序排列，以横向瀑布图/条形图展示。每个因子显示：当前值、相关系数、贡献占比、可调整滑块（联动 ROI 沙盘）。

#### 2.2.2 交互流程

```
DRill-Down 打开 → 自动请求 /diagnostic/{id} →
瀑布图渲染 8 项因子降序排列 →
Top 3 因子用红色高亮（贡献 > 10%） →
用户可拖动因子右侧滑块调整值 →
调整后实时重算离职概率（节流 100ms）
```

#### 2.2.3 验收标准

| # | 标准 | 指标 | 验证方法 |
|---|------|------|---------|
| AC1 | 瀑布图按 SHAP 贡献绝对值降序排列 | 第 1 项值 ≥ 第 2 项 ≥ ... | 检查 DOM 顺序 |
| AC2 | 后端 /diagnostic 接口响应时间 | < 200ms | curl -w "%{time_total}" |
| AC3 | Top 3 因子显性标注 | 红色字体/背景高亮 | 截图比对 |
| AC4 | 拖拽滑块节流 100ms | 松开后 100ms 内更新概率值 | Performance 录制 |
| AC5 | 因子面板与 ROI 沙盘数据联动 | 调薪因子变化→沙盘重算 | 联动测试 |

#### 2.2.4 数据契约

**请求**: `GET /api/v1/employees/{employee_id_hash}/diagnostic`

**响应**:
```json
{
  "code": 200,
  "data": {
    "employee_info": {
      "employee_id_hash": "57b8594cec78434525901c921c70522f",
      "display_alias": "李夏",
      "job_level": "P7",
      "department": "产研中心",
      "monthly_salary": 32000.0,
      "salary_growth_pct": 0.03,
      "performance_score": 4.2,
      "ona_centrality": 0.52,
      "total_turnover_prob": 0.717,
      "risk_level": "ORANGE"
    },
    "attribution_factors": [
      {
        "factor_name": "Salary_Increase_Pct",
        "factor_label": "近一年薪资涨幅停滞",
        "current_value": "3.0%",
        "coefficient": 0.198,
        "prob_contribution": 0.163
      }
    ]
  }
}
```

> 参考模型: `DiagnosticResponse` / `DiagnosticData` / `EmployeeExtendedProfile` / `AttributionFactor` (ona_models.py:279-351)

---

### 2.3 F3: Sandbox Interactive Simulator & PDF Export (沙盘推演与报告导出)

**ID**: F-ROI-SANDBOX  
**优先级**: P0  
**状态**: ✅ 已实现  

#### 2.3.1 功能描述

在个体诊断页右侧面板，提供交互式 ROI 模拟器。HR 拖动调薪滑块（0%–30%），系统实时计算：

- **Pre_Cost**: 当前离职概率 × 替换成本
- **Post_Cost**: 调薪后离职概率 × 替换成本
- **Invest_Cost**: 年度调薪投入（月薪差额 × 12）
- **Net_Savings**: Pre_Cost - Post_Cost - Invest_Cost

当 Net_Savings > 0 时，面板变为绿色（优选决策）；反之红色。

同时支持一键导出带 SHAP 图表 + ROI 测算的 Markdown/PDF 决策报告。

#### 2.3.2 交互流程

```
打开 EmployeeDrillDown → 右侧面板显示 ROI 沙盘 →
当前基线：离职概率 82% | 替换成本 ¥20,000 | 净节约 ¥0 →
HR 拖动"调薪幅度"滑块至 10% →
Throttle 100ms 后重算：
  · 新离职概率: ~20%
  · 投入: ¥15,600
  · 净节约: ¥2,520 ✅ 绿色 →
点击"导出 PDF" → 后端异步生成报告 → 浏览器新标签页打开
```

#### 2.3.3 验收标准

| # | 标准 | 指标 | 验证方法 |
|---|------|------|---------|
| AC1 | 滑块防抖/节流 100ms | Throttle 100ms 内不重复请求后端 | Performance Timing |
| AC2 | 动态重算级联留存收益 | 调薪后 cascade_effect 同步更新 | 对比调薪前后 cascadeEffect |
| AC3 | PDF 包含 SHAP 图表切片 | 至少 3 条归因因子 + 概率变化瀑布图 | 打开 PDF 目视验证 |
| AC4 | PDF 包含 ROI 测算表 | Pre/Post/Invest/Net 四列完整 | 打开 PDF 目视验证 |
| AC5 | 异步生成不阻塞主线程 | 主线程 FPS 波动 < 5fps | Performance 录制 |
| AC6 | Net_Savings > 0 时 UI 绿色 | 面板 background-color 切换 | inspect computed style |
| AC7 | 报告含页脚时间戳和保密声明 | "Generated: 2026-06-12" + "机密"水印 | 打开 PDF 目视验证 |

#### 2.3.4 数据契约

**ROI 模拟请求**: `POST /api/v1/ona/simulate/roi`
```json
{
  "employee_id_hash": "e48501815547b9698f09b81f3cca90de",
  "salary_increase_pct": 0.10
}
```

**ROI 模拟响应**:
```json
{
  "code": 200,
  "data": {
    "current_turnover_prob": 0.82,
    "proposed_turnover_prob": 0.198,
    "investment_cost": 15600.0,
    "benefit": 20064.0,
    "net_savings": 2520.0,
    "is_preferred_decision": true
  }
}
```

**PDF 导出**: `GET /api/v1/ona/report/{employee_id_hash}` → `StreamingResponse(application/pdf)`

> 参考模型: `RoiSimulationRequest` / `RoiSimulationResponse` / `RoiSimulationData` (ona_models.py:175-198)

---

### 2.4 F4: Data Import (CSV/Excel 批量导入)

**ID**: F-DATA-IMPORT  
**优先级**: P1  
**状态**: ✅ 已实现  

#### 2.4.1 功能描述

前端提供拖拽上传弹窗，支持 CSV 和 .xlsx 格式。后端解析 39 字段中文化映射，执行 bulk insert。

#### 2.4.2 验收标准

| # | 标准 | 指标 | 验证方法 |
|---|------|------|---------|
| AC1 | 支持 .csv 和 .xlsx 两种格式 | 2 种格式均返回 200 | 分别上传测试 |
| AC2 | 成功返回总行数/插入数/跳过数 | 返回 total/inserted/skipped | curl 验证 |
| AC3 | 重复 employee_id_hash 不报错（覆盖插入） | 二次上传同文件，更新而非崩溃 | 重复上传测试 |

> 参考模型: `OnaImportResponse` / `ImportResult` (ona_models.py:261-274)

---

### 2.5 F5: Intervention Management (干预记录管理)

**ID**: F-INTERVENTION  
**优先级**: P1  
**状态**: ✅ 已实现  

#### 2.5.1 数据契约

**创建干预**: `POST /api/v1/ona/intervention/create`
```json
{
  "employee_id_hash": "e48501815547b9698f09b81f3cca90de",
  "proposed_salary_increase": 0.10
}
```

> 参考模型: `InterventionCreateRequest` / `InterventionCreateResponse` (ona_models.py:147-169)

---

### 2.6 F6: LLM Playbook Engine (AI 面谈剧本生成)

**ID**: F-PLAYBOOK  
**优先级**: P2  
**状态**: ✅ 已实现  

#### 2.6.1 数据契约

**请求**: `POST /api/v1/ona/playbook/generate`
```json
{ "employee_id_hash": "e48501815547b9698f09b81f3cca90de" }
```

**响应**:
```json
{
  "code": 200,
  "data": {
    "markdown_content": "# ONA 组织网络纽带型干预剧本\n## ..."
  }
}
```

> 参考模型: `PlaybookGenerateRequest` / `PlaybookGenerateResponse` / `PlaybookData` (ona_models.py:203-218)

---

## 3. Data Schema Alignment

### 3.1 前端 ↔ 后端数据契约总览

| 前端组件 | 后端端点 | 响应模型 | 数据流向 |
|---------|---------|---------|---------|
| Dashboard (顶部预警) | `GET /` | 自有聚合 | 组件内聚合 |
| ONA Topology | `POST /subgraph` | `SubgraphResponse` | 中心节点 → G6 Graph |
| HoverTooltip | `POST /hover_details` | `ONAHoverResponse` | 节点 → 浮动弹窗 |
| EmployeeDrillDown | `GET /diagnostic` | `DiagnosticResponse` | 员工 → 归因面板 |
| ROISimulator | `POST /simulate/roi` | `RoiSimulationResponse` | 滑块值 → 重算结果 |
| DataUploadModal | `POST /upload` | `OnaImportResponse` | File → 导入结果 |
| PDF Export | `GET /report/{id}` | `StreamingResponse` | 员工 → PDF |
| PlaybookDrawer | `POST /playbook/generate` | `PlaybookGenerateResponse` | 员工 → 面谈剧本 |

### 3.2 核心实体关系

```
Employee (turnover.db)
  ├── employee_id_hash (PK, MD5)
  ├── display_alias
  ├── department, job_level
  ├── monthly_salary, salary_growth_pct
  ├── performance_score
  ├── monthly_working_hours, overtime_flag
  └── tenure_years, current_position_years
        │
        ▼
SHAP Engine ──→ attribution_factors[] (8 items)
ONA Engine ───→ eigenvector_centrality, hub_centrality
                 organization_shock_index
Cascade ──────→ cascade_effect_prediction
                 ├── direct_impact_nodes_count
                 ├── co_leaver_risk_multiplier
                 └── high_risk_connected_nodes[]
```

### 3.3 风险等级定义

| 等级 | 颜色 | 离职概率区间 | ONA 中心度要求 | 自动干预 |
|------|------|-------------|---------------|---------|
| RED (高危) | `#f5222d` | > 0.75 | ≥ 0.5 | 强制推送预警 |
| ORANGE (中危) | `#fa8c16` | 0.50–0.75 | 任意 | HRBP 手动确认 |
| YELLOW (低危) | `#fadb14` | 0.25–0.50 | 任意 | 观察名单 |
| GREEN (安全) | `#52c41a` | < 0.25 | 任意 | 无需动作 |

---

## 4. 术语表（Bilingual）

| 英文术语 | 中文术语 | 定义 |
|---------|---------|------|
| Eigenvector Centrality | 特征向量中心度 | 节点在网络中的"重要性"——连接越多高权重节点则中心度越高 |
| Hub Centrality | 枢纽中心度 | 节点作为信息传递中枢的能力 |
| Cascade Failure | 级联失效/连带流失 | 关键节点离职引发的邻接节点连锁离职 |
| Node Degree | 节点度 | 与该节点直接相连的邻居数量 |
| SHAP Attribution | SHAP 归因 | 基于 Shapley Value 的个体级特征贡献度分解 |
| Net Savings | 净节约金额 | 干预后预期损失 - 干预成本，正数=优选决策 |
| Organization Shock Index | 组织震荡指数 | 节点在整体网络中的枢纽百分位（0–1），越高则离职影响越广 |
| Replacement Cost | 替换成本 | 招聘花费 + 薪资溢价×12 + 隐性知识流失折算 |
| Ego Network | 自我中心网络 | 以特定节点为中心的子图（含一度/二度邻居） |
| Risk Exposure | 风险敞口 | 人才离职可能带来的财务损失总额 |
| Pulse Survey | 脉冲问卷/高频调研 | 竞品（Glint/Peakon）的核心数据采集方式 |
| Passive ONA | 被动式组织网络分析 | 基于协作日志的非干预式关系网络分析 |
| Co-Leaver Risk Multiplier | 连带流失风险倍率 | 关键节点离职对周围节点离职概率的放大系数 |
| Throttle | 节流 | 前端滑块拖动时控制接口调用频率的机制（100ms） |

---

## 5. 附录

### 5.1 项目文件结构

```
turnover-prediction/
├── api/
│   ├── main.py                    # 应用入口 + 路由注册
│   ├── models/ona_models.py       # Pydantic 数据模型（352 行）
│   ├── routers/
│   │   ├── ona_hover.py           # 悬停详情
│   │   ├── ona_diagnostic.py      # 员工诊断 + SHAP 归因
│   │   ├── ona_topology.py        # 拓扑与子图
│   │   ├── intervention.py        # 干预记录管理
│   │   ├── playbook.py            # LLM 面谈剧本
│   │   ├── ona_import.py          # 数据导入
│   │   └── report.py              # PDF 导出
│   └── services/
│       ├── db.py                  # 数据库操作
│       ├── shap_service.py        # SHAP 逻辑
│       └── roi_engine.py          # ROI 沙盘引擎
├── frontend/src/
│   ├── components/
│   │   ├── OnaTopology.jsx        # G6 拓扑图谱
│   │   ├── EmployeeDrillDown.jsx  # 员工诊断面板
│   │   ├── Dashboard.jsx          # 顶部预警看板
│   │   ├── DataUploadModal.jsx    # 数据导入弹窗
│   │   └── PlaybookDrawer.jsx     # 面谈剧本抽屉
│   └── api/ona.js                 # API 调用层
├── docs/
│   ├── product/
│   │   ├── competitive_analysis.md   # 竞品分析
│   │   ├── user_personas.md          # 用户画像
│   │   ├── product_roadmap.md        # 产品路线图
│   │   ├── cho_demo_script.md        # CHO 演示脚本
│   │   ├── pricing_strategy.md       # 定价策略
│   │   ├── implementation_guide.md   # 实施指南
│   │   ├── data_import_spec.md       # 数据导入规范
│   │   └── import_field_mapping.md   # 字段中英文对照表
│   └── ... （技术文档 8 份）
└── turnover.db                    # SQLite 数据库
```

### 5.2 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| v0.3.0 | 2026-06-12 | MVP 闭环：数据导入 → ONA 诊断 → SHAP → ROI → PDF 导出 |
| v0.2.0 | 2026-05 | 核心数据管道打通：SQLite 集成 + ONA 基础功能 |
| v0.1.0 | 2026-04 | 原型验证：拓扑图谱 + 悬停弹窗 |

### 5.3 参考资料

- [竞品分析报告](competitive_analysis.md) — Workday Peakon / Visier / Glint / Culture Amp 对比
- [用户画像](user_personas.md) — HRBP / CHO 深度场景分析
- [产品路线图](product_roadmap.md) — 迭代计划和里程碑
- [ONA OpenAPI v1](ona-openapi-v1.md) — API 接口规范
- [数据字典](data_pipeline_and_dictionary_spec.md) — 39 字段定义
