import { EMPLOYEE_REGISTRY, SHEN_HASH } from './employeeRegistry';

/**
 * ONA 拓扑图 — 子图 Mock 数据
 * 基于 EMPLOYEE_REGISTRY 构建
 */
export function buildSubgraphMock(centerId, depth = 2) {
  const allNodes = Object.entries(EMPLOYEE_REGISTRY).map(([id, e]) => ({
    id,
    label: e.name,
    size: id === SHEN_HASH ? 45 : 28,
    style: id === SHEN_HASH ? { fill: '#FF4D4F', stroke: '#FF4D4F', lineWidth: 2 } : undefined,
    description: `${e.department} · ${e.position}`,
  }));

  const registryKeys = Object.keys(EMPLOYEE_REGISTRY);
  const allEdges = [];
  for (let i = 0; i < registryKeys.length; i++) {
    for (let j = i + 1; j < registryKeys.length; j++) {
      if (j - i <= 3) {
        allEdges.push({ source: registryKeys[i], target: registryKeys[j] });
      }
    }
  }

  const visited = new Set([centerId]);
  const queue = [{ id: centerId, level: 0 }];
  for (let i = 0; i < queue.length; i++) {
    const { id, level } = queue[i];
    if (level >= depth) continue;
    for (const edge of allEdges) {
      let neighbor = null;
      if (edge.source === id) neighbor = edge.target;
      else if (edge.target === id) neighbor = edge.source;
      if (neighbor && !visited.has(neighbor)) {
        visited.add(neighbor);
        queue.push({ id: neighbor, level: level + 1 });
      }
    }
  }

  const nodes = allNodes.filter(n => visited.has(n.id));
  const nodeSet = new Set(nodes.map(n => n.id));
  const edges = allEdges.filter(e => nodeSet.has(e.source) && nodeSet.has(e.target));

  return { nodes, edges };
}
