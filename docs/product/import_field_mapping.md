# 员工数据导入 - 必填字段中英文对照表

**说明**: 上传的 Excel/CSV 文件第一行必须是英文列名。本表列出每个英文列名的中文含义、填写格式和可选值。

| 英文列名 | 中文含义 | 类型 | 示例值 | 可选值 / 备注 |
|---------|---------|------|--------|-------------|
| `Age` | 年龄 | 整数 | `35` | 18 – 70 |
| `Attrition` | 是否离职 | 枚举 | `No` | `No` 在岗 · `Yes` 已离职 |
| `BusinessTravel` | 出差频率 | 枚举 | `Travel_Frequently` | `Travel_Frequently` 频繁 · `Travel_Rarely` 偶尔 · `Non-Travel` 不出差 |
| `Department` | 部门 | 枚举/文本 | `Research & Development` | `Research & Development` → 数智人力事业部 · `Sales` → 数智营销事业部 · `Human Resources` → 人力资源中心；如不在表中则原样保留 |
| `Education` | 学历等级 | 整数 | `4` | 1=高中 · 2=大专 · 3=本科 · 4=硕士 · 5=博士 |
| `EducationField` | 所学专业 | 文本 | `Computer Science` | 如 Computer Science, Marketing, 人力资源 等 |
| `Gender` | 性别 | 枚举 | `Male` | `Male` 男 · `Female` 女 |
| `JobLevel` | 职级 | 整数 | `3` | 1=P1–P3 · 2=P4–P5 · 3=P6–P7 · 4=P8–P9 · 5=P10+ |
| `JobRole` | 岗位 | 枚举/文本 | `Research Scientist` | `Research Scientist` → 高级算法工程师 · `Laboratory Technician` → 实验室技术员 · `Manager` → 高级产品经理 · `Sales Executive` → 高级销售顾问 · `Manufacturing Director` → 制造总监 · `Sales Representative` → 售前顾问 · `Research Director` → 技术总监 · `Human Resources` → HRBP · `Healthcare Representative` → 医疗行业顾问；如不在表中则原样保留 |
| `MaritalStatus` | 婚姻状况 | 枚举 | `Married` | `Married` 已婚 · `Single` 未婚 · `Divorced` 离异 |
| `MonthlyIncome` | 月薪（元） | 整数 | `32000` | 税前月薪 |
| `OverTime` | 是否常加班 | 枚举 | `No` | `No` 不常加班 · `Yes` 经常加班 |
| `PercentSalaryHike` | 最近薪资涨幅 | 整数 | `15` | 百分比，如 15 表示涨薪 15% |
| `PerformanceRating` | 绩效评级 | 整数 | `4` | 1=不及格 · 2=中等 · 3=良好 · 4=优秀 · 5=卓越 |
| `TotalWorkingYears` | 总工龄（年） | 小数 | `12` | 可带小数 |
| `YearsAtCompany` | 本公司工龄（年） | 小数 | `6` | 可带小数 |
| `YearsInCurrentRole` | 现岗位年限（年） | 小数 | `4` | 可带小数 |
| `YearsSinceLastPromotion` | 距上次晋升年数 | 整数 | `3` | — |

## 常见问题

**Q: 列名必须完全一样吗？**
A: 是。`MonthlyIncome` 不能写成 `Monthly income` 或 `月薪`。建议直接从模板复制列名。

**Q: Department / JobRole 用中文可以吗？**
A: 可以。系统优先匹配内置映射表，没有匹配的会原样保留。例如填「产研中心」→ 入库后就是「产研中心」。

**Q: 有空值会怎样？**
A: 该行会跳过并被计入"跳过/错误"计数，不影响其他行。

**Q: 可以批量上传重复数据吗？**
A: 系统按 `employee_id_hash` 自动去重，重复上传的数据会覆盖更新。
