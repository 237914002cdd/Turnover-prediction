# ONA 留任决策平台 — OpenAPI v1 对接规范

版本: v1
基础 URL: `http://<host>:8000`
数据格式: `application/json`
鉴权: Bearer JWT（预留）

---

## 1. 节点悬停详情

获取拓扑图中指定节点的风险画像、SHAP 归因因子、级联流失预测。

```
POST /api/v1/ona/node/hover_details
```

**请求体:**
```json
{ "employee_id_hash": "e10adc3949ba59abbe56e057f20f883e" }
```

**响应体:**
```json
{
  "code": 200,
  "data": {
    "node_info": { "employee_id_hash": "...", "display_alias": "员工-申鹏程", "department": "技术研发部-架构组", "job_level": "P5", "tenure_years": 1.5 },
    "risk_metrics": { "final_risk_level": "RED", "base_turnover_probability": 0.82, "ona_centrality_score": 0.96, "total_replacement_cost_cny": 25000.0 },
    "shap_risk_factors": [
      { "factor_name": "Salary_Increase_Pct", "factor_label": "近一年薪资涨幅停滞", "shap_value": 0.35, "current_value": "0.0%" }
    ],
    "cascade_effect_prediction": { "direct_impact_nodes_count": 3, "total_downstream_risks_count": 10, "co_leaver_risk_multiplier": 2.4 }
  }
}
```

---

## 2. ROI 实时模拟

HR 拖动调薪滑块时触发，后端计算 P_new 和财务损益后返回。

```
POST /api/v1/roi/simulate
```

**请求体:**
```json
{ "employee_id_hash": "e10adc3949ba59abbe56e057f20f883e", "salary_increase_pct": 0.12 }
```

**响应体:**
```json
{
  "code": 200,
  "data": {
    "current_turnover_prob": 0.82,
    "proposed_turnover_prob": 0.46,
    "investment_cost": 18720.0,
    "benefit": 8976.08,
    "net_savings": -9743.92,
    "is_preferred_decision": false
  }
}
```

**公式:** `P_new = P_base × e^(-α × X)` | `Net_Savings = (P_base - P_new) × ReplaceCost - InvestCost`

---

## 3. 员工诊断归因矩阵

```
GET /api/v1/employee/diagnostic/{employee_id_hash}
```

**响应体:**
```json
{
  "code": 200,
  "data": {
    "employee_info": { "age": 29, "gender": "男", "education": "硕士研究生", "job_level": "P7", "monthly_salary": 18000.0, "total_turnover_prob": 0.717, "risk_level": "ORANGE" },
    "attribution_factors": [
      { "factor_name": "salary_growth", "factor_label": "薪资增幅", "current_value": "3%", "coefficient": 0.198, "prob_contribution": 0.163 }
    ]
  }
}
```

---

## 4. 创建干预（状态机）

```
POST /api/v1/ona/intervention/create
```

**请求体:**
```json
{ "employee_id_hash": "e10adc3949ba59abbe56e057f20f883e", "proposed_salary_increase": 0.12 }
```

**响应体:**
```json
{
  "code": 200,
  "data": {
    "record_id": 6262881,
    "current_status": "IN_PROGRESS",
    "silence_until": "2026-07-09",
    "net_savings": 2520.0,
    "is_positive_roi": true
  }
}
```

**状态机流转:** `NEW → IN_PROGRESS → RESOLVED | FALSE_POSITIVE | TURNOVER`

---

## 5. Ego Network 子图

```
GET /api/v1/ona/graph/subgraph?center_employee_id_hash=e10adc...&depth=2
```

**响应体:**
```json
{
  "code": 200,
  "data": {
    "nodes": [{ "id": "e10adc...", "label": "申鹏程", "size": 45 }],
    "edges": [{ "source": "e10adc...", "target": "c4ca42..." }],
    "total": 6
  }
}
```

**算法:** BFS 邻接搜索，depth=1 一阶, depth=2 二阶。生产环境用 Recursive CTE。

---

## 6. LLM 面谈剧本生成

```
POST /api/v1/ona/playbook/generate
```

**请求体:**
```json
{ "employee_id_hash": "e10adc3949ba59abbe56e057f20f883e" }
```

**响应体:**
```json
{
  "code": 200,
  "data": {
    "markdown_content": "## 👥 1. 面谈心理破冰策略\n..."
  }
}
```

---

## 示例：飞书/钉钉机器人集成流程

```
1. 飞书机器人接收 HR 指令: "查询申鹏程离职风险"
2. 调用 POST /api/v1/ona/node/hover_details
3. 风险等级 RED → 自动推送消息卡
4. 调用 GET /api/v1/ona/graph/subgraph 获取关联同事
5. 结果以飞书消息卡片形式返回
```

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1 | 2026-06-10 | 初始 6 端点规范 |
