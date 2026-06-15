# 数据导入模板填写说明

**文档版本**: v1.0 · 2026-06-12  
**适用对象**: HR 人员  
**导入方式**: 在 ONA 平台点击「批量导入员工数据」，上传填写好的 .xlsx 或 .csv 文件

---

## 模板文件

模板文件位于平台前端页面 → 点击「批量导入员工数据」→ 点击「下载导入模板」按钮。

---

## 字段说明

共 18 个字段，全部必填。第一行为英文列名，从第二行开始填数据。

| # | 列名 | 中文含义 | 填写说明 | 可选值示例 |
|---|------|---------|---------|-----------|
| 1 | `Age` | 年龄 | 整数，18–70 | `35` |
| 2 | `Attrition` | 是否离职 | 当前在职填 `No`，已离职填 `Yes` | `No` / `Yes` |
| 3 | `BusinessTravel` | 出差频率 | 高频填 `Travel_Frequently`，偶尔填 `Travel_Rarely`，不出差填 `Non-Travel` | `Travel_Frequently` |
| 4 | `Department` | 部门名称 | 可选值见下方 | `Research & Development` |
| 5 | `Education` | 学历等级 | 1=高中，2=大专，3=本科，4=硕士，5=博士 | `4` |
| 6 | `EducationField` | 所学专业 | 如 Computer Science, Marketing, HR 等 | `Computer Science` |
| 7 | `Gender` | 性别 | `Male`=男，`Female`=女 | `Male` |
| 8 | `JobLevel` | 职级 | 1=P1–P3，2=P4–P5，3=P6–P7，4=P8–P9，5=P10+ | `3` |
| 9 | `JobRole` | 岗位名称 | 可选值见下方 | `Research Scientist` |
| 10 | `MaritalStatus` | 婚姻状况 | `Married`=已婚，`Single`=未婚，`Divorced`=离异 | `Married` |
| 11 | `MonthlyIncome` | 月薪（元） | 整数，税前月薪 | `32000` |
| 12 | `OverTime` | 是否经常加班 | `Yes`=经常，`No`=不经常 | `No` |
| 13 | `PercentSalaryHike` | 最近薪资涨幅（%） | 整数，如 15 表示最近涨薪 15% | `15` |
| 14 | `PerformanceRating` | 绩效评级 | 1=不及格，2=中等，3=良好，4=优秀，5=卓越 | `4` |
| 15 | `TotalWorkingYears` | 总工龄（年） | 小数或整数 | `12` |
| 16 | `YearsAtCompany` | 本公司工龄（年） | 小数或整数 | `6` |
| 17 | `YearsInCurrentRole` | 现岗位年限（年） | 小数或整数 | `4` |
| 18 | `YearsSinceLastPromotion` | 距离最近晋升年数（年） | 整数 | `3` |

---

## 可选值参考

### Department（部门）

| 列中填写 | 平台自动映射为 |
|---------|-------------|
| `Research & Development` | 用友网络 - 数智人力事业部 |
| `Sales` | 数智营销事业部 |
| `Human Resources` | 人力资源中心 |

### JobRole（岗位）

| 列中填写 | 平台自动映射为 |
|---------|-------------|
| `Research Scientist` | 高级算法工程师 |
| `Laboratory Technician` | 实验室技术员 |
| `Manager` | 高级产品经理 |
| `Sales Executive` | 高级销售顾问 |
| `Manufacturing Director` | 制造总监 |
| `Sales Representative` | 售前顾问 |
| `Research Director` | 技术总监 |
| `Human Resources` | HRBP |
| `Healthcare Representative` | 医疗行业顾问 |

### 如果部门或岗位不在上表中

直接填中文名也可以，平台会原样保留。例如 `Department` 填「产研中心」→ 入库后显示「产研中心」。

---

## 注意事项

1. **必填**: 18 个字段**不能有空值**，否则该行会跳过
2. **列名必须完全匹配**: 大小写敏感，如 `MonthlyIncome` 不能写成 `Monthly income` 或 `月薪`
3. **编码**: .csv 文件请使用 UTF-8 编码保存
4. **重复导入**: 系统会根据 `employee_id_hash` 自动去重，不会重复计数
5. **一次最多**: 单次上传建议不超过 10,000 行

---

## 常见错误

| 报错信息 | 原因 | 解决 |
|---------|------|------|
| "缺少必填字段" | 列名拼写错误或缺失 | 核对模板中的列名，完全一致 |
| "文件解析失败" | 非法格式或编码不对 | 另存为 UTF-8 编码的 .csv 或标准 .xlsx |
| "不支持的文件格式" | 上传了 .pdf/.txt 等 | 只能上传 .csv 或 .xlsx |
