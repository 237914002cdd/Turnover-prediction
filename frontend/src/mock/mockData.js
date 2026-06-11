import { EMPLOYEE_REGISTRY, SHEN_HASH } from './employeeRegistry';

const riskLevelColors = {
  RED: '#FF4D4F',
  ORANGE: '#FA8C16',
  YELLOW: '#FADB14',
  GREEN: '#52C41A',
};

export const riskLevelColor = (level) => riskLevelColors[level] || '#999';

export const mockGraphData = {
  nodes: Object.entries(EMPLOYEE_REGISTRY).map(([id, e]) => ({
    id,
    label: e.name,
    size: id === SHEN_HASH ? 45 : 28,
    style: id === SHEN_HASH ? { fill: '#FF4D4F', stroke: '#FF4D4F', lineWidth: 2 } : undefined,
    description: `${e.department} · ${e.position}`,
  })),
  edges: (() => {
    const keys = Object.keys(EMPLOYEE_REGISTRY);
    const edges = [];
    for (let i = 0; i < keys.length; i++) {
      for (let j = i + 1; j < keys.length; j++) {
        if (j - i <= 3) {
          edges.push({ source: keys[i], target: keys[j] });
        }
      }
    }
    return edges;
  })(),
};
