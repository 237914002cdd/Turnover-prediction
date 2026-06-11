/**
 * ONA 拓扑图 — API 网络层
 *
 * 统一的 Axios 实例，指向 FastAPI 后端。
 * 所有 ONA/ROI 相关的接口调用统一在此封装。
 */
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
});

/** 获取 ONA 节点悬停详情 */
export async function fetchOnaNodeDetails(employeeIdHash) {
  const resp = await api.post('/api/v1/ona/node/hover_details', {
    employee_id_hash: employeeIdHash,
  });
  return resp.data;
}

/** 创建干预记录（状态机 NEW → IN_PROGRESS） */
export async function createIntervention(employeeIdHash, salaryIncreasePct) {
  const resp = await api.post('/api/v1/ona/intervention/create', {
    employee_id_hash: employeeIdHash,
    proposed_salary_increase: salaryIncreasePct,
  });
  return resp.data;
}

/** ROI 实时模拟测算（后端物理引擎重算） */
export async function simulateRoi(employeeIdHash, salaryIncreasePct) {
  const resp = await api.post('/api/v1/roi/simulate', {
    employee_id_hash: employeeIdHash,
    salary_increase_pct: salaryIncreasePct,
  });
  return resp.data;
}

/** 获取 LLM 生成的面谈干预剧本 (Playbook) */
export async function fetchPlaybook(employeeIdHash) {
  const resp = await api.post('/api/v1/ona/playbook/generate', {
    employee_id_hash: employeeIdHash,
  });
  return resp.data;
}

/** 获取 Ego Network 子图（一阶/二阶邻接） */
export async function fetchSubgraph(centerEmployeeIdHash, depth = 2) {
  const resp = await api.get('/api/v1/ona/graph/subgraph', {
    params: { center_employee_id_hash: centerEmployeeIdHash, depth },
  });
  return resp.data;
}

/** 获取员工诊断归因矩阵（39 字段 + 8 项归因因子） */
export async function fetchDiagnostic(employeeIdHash) {
  const resp = await api.get(`/api/v1/employee/diagnostic/${employeeIdHash}`);
  return resp.data;
}

/** 上传 CSV/Excel 批量导入员工数据 */
export async function uploadCsv(file) {
  const formData = new FormData();
  formData.append('file', file);
  const resp = await fetch('http://localhost:8000/api/v1/ona/graph/upload', {
    method: 'POST',
    body: formData,
  });
  return resp.json();
}

export default api;
