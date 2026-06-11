/**
 * ONA 拓扑图 — Mock 数据（拓扑布局专用）
 *
 * 悬停 API 请求已迁移至 `src/api/ona.js` 直接发起网络请求。
 * 本文件仅保留拓扑图节点/边布局数据，供 G6 画布初始渲染使用。
 */

// ===== 拓扑图节点/边 =====
export const mockGraphData = {
  nodes: [
    {
      id: 'e10adc3949ba59abbe56e057f20f883e',
      label: '申鹏程',
      size: 45,
      style: { fill: '#FF4D4F', stroke: '#FF4D4F', lineWidth: 2 },
      description: '技术研发部架构组 · P5',
    },
    { id: 'c4ca4238a0b923820dcc509a6f75849b', label: '员工B', size: 28, description: '核心研发' },
    { id: 'c81e728d9d4c2f636f067f89cc14862c', label: '员工C', size: 28, description: '产品经理' },
    { id: 'eccbc87e4b5ce2fe28308fd9f2a7baf3', label: '员工D', size: 28, description: '测试骨干' },
    { id: 'a87ff679a2f3e71d9181a67b7542122c', label: '员工E', size: 24, description: '前端开发' },
    { id: 'e4da3b7fbbce2345d7772b0674a318d5', label: '员工F', size: 24, description: '后端开发' },
    { id: '1679091c5a880faf6fb5e6087eb1b2dc', label: '员工G', size: 24, description: 'UI 设计' },
    { id: '8f14e45fceea167a5a36dedd4bea2543', label: '员工H', size: 24, description: 'DevOps' },
    { id: 'c9f0f895fb98ab9159f51fd0297e236d', label: '员工I', size: 20, description: '实习生' },
    { id: 'd3d9446802a44259755d38e6ebd4c1b2', label: '员工J', size: 20, description: '售前支持' },
    { id: '6512bd43d9caa6e02c990b0a82652d0b', label: '员工K', size: 20, description: '产品运营' },
    { id: 'c20ad4d76fe97759aa27a0c99bff6710', label: '员工L', size: 20, description: '数据分析' },
  ],
  edges: [
    { source: 'e10adc3949ba59abbe56e057f20f883e', target: 'c4ca4238a0b923820dcc509a6f75849b' },
    { source: 'e10adc3949ba59abbe56e057f20f883e', target: 'c81e728d9d4c2f636f067f89cc14862c' },
    { source: 'e10adc3949ba59abbe56e057f20f883e', target: 'eccbc87e4b5ce2fe28308fd9f2a7baf3' },
    { source: 'e10adc3949ba59abbe56e057f20f883e', target: 'c9f0f895fb98ab9159f51fd0297e236d' },
    { source: 'e10adc3949ba59abbe56e057f20f883e', target: 'd3d9446802a44259755d38e6ebd4c1b2' },
    { source: 'c4ca4238a0b923820dcc509a6f75849b', target: 'e4da3b7fbbce2345d7772b0674a318d5' },
    { source: 'c4ca4238a0b923820dcc509a6f75849b', target: 'a87ff679a2f3e71d9181a67b7542122c' },
    { source: 'c81e728d9d4c2f636f067f89cc14862c', target: '1679091c5a880faf6fb5e6087eb1b2dc' },
    { source: 'c81e728d9d4c2f636f067f89cc14862c', target: '6512bd43d9caa6e02c990b0a82652d0b' },
    { source: 'eccbc87e4b5ce2fe28308fd9f2a7baf3', target: '8f14e45fceea167a5a36dedd4bea2543' },
    { source: 'eccbc87e4b5ce2fe28308fd9f2a7baf3', target: 'c20ad4d76fe97759aa27a0c99bff6710' },
    { source: 'a87ff679a2f3e71d9181a67b7542122c', target: 'c9f0f895fb98ab9159f51fd0297e236d' },
    { source: 'd3d9446802a44259755d38e6ebd4c1b2', target: '6512bd43d9caa6e02c990b0a82652d0b' },
    { source: 'c20ad4d76fe97759aa27a0c99bff6710', target: 'e4da3b7fbbce2345d7772b0674a318d5' },
  ],
};

// ===== 颜色映射 =====
const riskLevelColors = {
  RED: '#FF4D4F',
  ORANGE: '#FA8C16',
  YELLOW: '#FADB14',
  GREEN: '#52C41A',
};

export const riskLevelColor = (level) => riskLevelColors[level] || '#999';
