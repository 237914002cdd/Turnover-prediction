# Turnover Prediction Project - Architectural Refactor Task

Execute full architectural refactor for the turnover-prediction project. 
We need to eliminate all hardcoded data contradictions, unify our mock data, and fix the mathematical logic across components based on our Master PRD Specification.

## [CRITICAL INSTRUCTION: PATH GOVERNOR]
- Keep all modifications strictly within your designated workspace folder (typically on your D: drive project path). Do not escape.

## [TASK 1: Unify the Employee Registry (Single Source of Truth)]
1. Locate `mockData.js`, `subgraphMock.js`, and `OnaTopology.jsx`. Extract all scattered mock objects into a centralized registry array or object named `EMPLOYEE_REGISTRY`.
2. Ensure key employee attributes strictly conform to our Data Schema (Employee_ID, Age, Tenure_Years, Monthly_Income, Salary_Increase_Pct, Performance_Score).
3. Align Shen Pengcheng's ('e48501815547b9698f09b81f3cca90de') and Li Xia's ('57b8594cec78434525901c921c70522f') baseline metrics to match the Master PRD core case:
   - For Shen Pengcheng (Employee A): Monthly_Income: 13000, marketSalary: 15000, recruitmentCost: 1000, originalRisk: 80, Tenure_Years: 1.5, position: "高级算法工程师", department: "用友网络 - 数智人力事业部", maxNetworkImpact: 12.
4. Update ALL hover cards, topology tooltips, and detail sidebars to dynamic lookups: `EMPLOYEE_REGISTRY[targetHash]`. Fix the bug where position strings or corporate paths accidentally overwrite the pure employee name state.

## [TASK 2: Dynamic Formulas & Logic Correction]
1. Fix Domino Cascade Count: In the hover tooltip/card, do not hardcode "预计连带影响 12 人". Replace it with a dynamic variable based on the node's network attributes or use `node.maxNetworkImpact` from our registry.
2. Fix ROI Paradox: In the retention simulation sandbox, change the formula for `预期流失挽回收益` (Expected Savings). It must be mathematically bound to our PRD ROI engine formula:
   - Pre-intervention cost = (originalRisk / 100) * (recruitmentCost + (marketSalary - Monthly_Income) * 12)
   - Post-intervention cost = (currentRisk / 100) * (recruitmentCost + (marketSalary - currentMonthlyIncome) * 12)
   - Investment = (currentMonthlyIncome - Monthly_Income) * 12
   - Savings (净节约金额) = Pre-intervention cost - Post-intervention cost - Investment
   Ensure savings can NEVER illegally exceed the maximum replacement cost or produce logical paradoxes.

## [TASK 3: Global State Relay for Top Bar]
1. Establish a simple state mechanism (or context callback) so that when an employee's risk rate is modified inside the Sandbox, the parent state is notified.
2. The top bar statistics ("高风险人才总期望替换损失" and "预警概览") must be reactive computed values. If Shen Pengcheng's risk drops from 80% to 20%, the global replacement cost bar must adaptively subtract the averted loss based on the reactive compute loop.

Refactor clean, verify there are 0 build errors, and make sure our 9-grid renders both "申鹏程" and "李夏" using their fresh centralized registry names. Go!
