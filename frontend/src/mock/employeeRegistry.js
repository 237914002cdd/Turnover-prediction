/**
 * 统一员工注册表（EMPLOYEE_REGISTRY）
 * 所有组件的员工数据唯一源，取代散落在各 Mock 文件中的硬编码。
 *
 * 申鹏程 & 李夏 的基线严格对齐 Master PRD V4.0。
 */

// ===== 锚点哈希 =====
export const SHEN_HASH = 'e48501815547b9698f09b81f3cca90de';
export const LIXIA_HASH = '57b8594cec78434525901c921c70522f';

// ===== 员工注册表 =====
export const EMPLOYEE_REGISTRY = {
  [SHEN_HASH]: {
    hash: SHEN_HASH,
    name: '申鹏程',
    age: 32,
    position: '高级算法工程师',
    department: '用友网络 - 数智人力事业部',
    jobLevel: 'P5',
    monthlyIncome: 13000,
    marketSalary: 15000,
    recruitmentCost: 1000,
    originalRisk: 0.80,         // 80%
    salaryGrowthPct: 0,          // 0%
    tenureYears: 1.5,
    performanceScore: 4.5,
    maxNetworkImpact: 12,        // 级联影响人数
    onaCentrality: 0.96,
    riskLevel: 'HIGH',
    performanceLevel: 'HIGH',
    managementTag: '隐形组织章鱼 / 高负载错配',
  },
  [LIXIA_HASH]: {
    hash: LIXIA_HASH,
    name: '李夏',
    age: 29,
    position: '高级产品经理',
    department: '用友网络 - 数智人力事业部',
    jobLevel: 'P7',
    monthlyIncome: 32000,
    marketSalary: 42000,
    recruitmentCost: 1500,
    originalRisk: 0.717,         // 71.7%
    salaryGrowthPct: 0.03,       // 3%
    tenureYears: 6,
    performanceScore: 4.2,
    maxNetworkImpact: 8,
    onaCentrality: 0.62,
    riskLevel: 'MID',
    performanceLevel: 'HIGH',
    managementTag: '核心高危高产钻石',
  },
};

/** 获取员工显示名 */
export function getEmployeeName(hash) {
  return EMPLOYEE_REGISTRY[hash]?.name || null;
}

/** 九宫格派生数据 */
export function buildGridData() {
  return Object.values(EMPLOYEE_REGISTRY).map(e => ({
    label: e.name,
    riskLevel: e.riskLevel,
    perf: e.performanceScore,
    dept: e.department,
  }));
}
