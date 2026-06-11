# ONA 拓扑图 — 悬停弹窗前端渲染规范

**文档版本**: v1.0 · 对应 Master PRD V4.0 第五章第 1 节  
**接口协议**: `POST /api/v1/ona/node/hover_details`  
**响应时限要求**: 悬停 → 弹窗完整渲染 ≤ **150ms**

---

## 1. UI 组件架构

悬停弹窗 (Hover Tooltip Component) 分 5 个区域，自顶向下：

```
┌──────────────────────────────────────────────────┐
│  [RED]  员工-申鹏程 (脱敏标识)          ⚠ 高危  │  ← 顶部状态条
├──────────────────────────────────────────────────┤
│  离职概率  82%    震荡指数  Top 2%    替换成本   │  ← 核心指标卡
│                      (组织震荡)     ¥25,000     │
├──────────────────────────────────────────────────┤
│  ┌ 归因瀑布图 ──────────────────────────────┐   │
│  │ Salary_Increase_Pct    ■■■■■■■■■■ 0.35  │   │  ← SHAP 因子
│  │ Overtime_Hours         ■■■■■■■■  0.28   │   │     降序排列
│  │ YearsAtCompany         ■■■■■    0.19    │   │
│  └──────────────────────────────────────────┘   │
├──────────────────────────────────────────────────┤
│  ⚠ 联动预警: 该节点离职将使周边 10 人风险      │   │  ← 级联流失
│  上升 2.4 倍 (直接关联: 3 人)                   │   │     预警区
│  [员工B] ████████████████  YELLOW  142次/月     │
│  [员工C] █████████████    GREEN    98次/月      │
│  [员工D] ████████████     YELLOW   85次/月      │
├──────────────────────────────────────────────────┤
│  [一键干预剧本]  ONA 组织网络纽带型             │   │  ← 底部按钮
└──────────────────────────────────────────────────┘
```

---

## 2. JSON → UI 字段映射表

| 前端 UI 区域 / 槽位 | JSON 路径 | 渲染规则与样式 |
|---|---|---|
| **弹窗顶部色条** | `data.risk_metrics.final_risk_level` | `RED=#FF4D4F` / `ORANGE=#FA8C16` / `YELLOW=#FADB14` / `GREEN=#52C41A`；RED 需加 500ms 呼吸闪烁动画 |
| **员工标识行** | `data.node_info.display_alias` | 字号 14px，加粗；左侧显示部门标签 `data.node_info.department` 为 tag |
| **职级+司龄** | `data.node_info.job_level` / `tenure_years` | 灰色副文本，格式 `P5 · 1.5年` |
| **绩效分** | `data.node_info.performance_score` | 星标或数字渲染，≥4.0 加金色高亮 |
| **离职概率** | `data.risk_metrics.base_turnover_probability` | 转为百分比 `82%`，配合半圆仪表盘或数字大字号突出 |
| **ONA 中心度** | `data.risk_metrics.ona_centrality_score` | 短进度条渲染，≥0.7 时进度条变红色 |
| **组织震荡指数** | `data.risk_metrics.organization_shock_index` | 转为 `Top X%`，带 ⚡ 图标；≥0.9 加闪烁 |
| **替换成本** | `data.risk_metrics.total_replacement_cost_cny` | 格式化为 `¥25,000`，货币符号加粗 |
| **SHAP 瀑布图** | `data.shap_risk_factors[]` | 遍历数组，柱状图长度由 `shap_value` 绝对值决定；标签显示 `factor_label`；右侧显示 `current_value` |
| **级联直接人数** | `data.cascade_effect_prediction.direct_impact_nodes_count` | 数字加粗 + "人" |
| **下游总风险** | `data.cascade_effect_prediction.total_downstream_risks_count` | 数字标红 |
| **倍率** | `data.cascade_effect_prediction.co_leaver_risk_multiplier` | 格式 `X.X 倍`，≥2.0 加橙色警告 |
| **邻接节点列表** | `data.cascade_effect_prediction.high_risk_connected_nodes[]` | 每行: 缩略头像 + 名称 + 风险色块 + 频次进度条 |
| **邻接节点风险色** | `[].current_risk_level` | 同上颜色映射，左侧 4px 竖条 |
| **按钮标签** | `data.matched_playbook.strategy_title` | `el-button` 或自定义按钮 |
| **展开清单** | `data.matched_playbook.action_items[]` | 点击按钮后展开有序列表 |

---

## 3. 交互行为规范

### 3.1 悬停
- 鼠标悬停在拓扑图节点上 ≥ **200ms**（防抖）触发 API 请求
- 请求发出后 **150ms 内** 弹窗必须完全渲染
- 弹窗位置：节点正上方偏右，避免遮挡邻接边
- 弹窗出现时，拓扑图主画布：悬停节点保持原有颜色，其 **一阶 + 二阶邻接边变红(饱和度高)**，其余节点透明度 → `0.1`

### 3.2 移出
- 鼠标移出弹窗区域后 **300ms** 弹窗自动关闭
- 关闭时邻接边恢复原始样式，所有节点透明度恢复 `1.0`
- 若鼠标从节点直接移到弹窗，不倒计时关闭（弹窗可 hover）

### 3.3 点击
- 点击弹窗底部「一键干预剧本」→ 展开 action_items 列表（不跳转页面）
- 点击弹窗外灰色蒙层 / 按 ESC → 关闭弹窗

---

## 4. 前端组件推荐

| 需求 | 推荐库 | 理由 |
|---|---|---|
| ONA 拓扑图 | AntV G6 v5 / Cytoscape.js | 原生支持力导向布局 + 节点样式动态切换 |
| SHAP 瀑布图 | ECharts 柱状图 / D3.js | 水平条形图+标签，轻量 |
| 悬停弹窗 | 自定义 Tooltip 组件 (Vue/React) | 完全控制动画与布局 |
| 状态管理 | Pinia (Vue) / Zustand (React) | 缓存已拉取的节点数据，减少重复请求 |

---

## 5. 降级与错误处理

| 场景 | 行为 |
|---|---|
| API 返回 `code != 200` | 弹窗仍显示，内容展示 "数据加载失败，请重试"，邻接节点不高亮 |
| `shap_risk_factors` 为空数组 | 隐藏 SHAP 瀑布图区域，弹窗显示 "暂无可解释性因子" |
| `high_risk_connected_nodes` 为空 | 隐藏级联预警区，仅显示 "该节点网络关联度低" |
| 网络超时 (≥1000ms) | 弹窗展示骨架屏(Skeleton)，5s 后提示超时，不强刷 |
| 鼠标快速划过多个节点 | 只对最后 hover 的节点发起请求，前面的请求被 cancel（AbortController） |

---

## 6. 性能约束清单

| 指标 | 目标值 | 测量方式 |
|---|---|---|
| 悬停→API 请求发出 | ≤ 50ms | 前端 performance.mark |
| API P99 响应时间 | ≤ 80ms | 服务端监控 |
| JSON 解析+DOM 渲染 | ≤ 20ms | React/Vue DevTools |
| **端到端总耗时** | **≤ 150ms** | 合成监控 |
| 弹窗关闭→画布恢复 | ≤ 100ms | requestAnimationFrame 回调 |
