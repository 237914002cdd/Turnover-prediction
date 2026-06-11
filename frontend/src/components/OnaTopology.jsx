import React, { useEffect, useRef, useState, useCallback } from 'react';
import G6 from '@antv/g6';
import { debounce } from 'lodash';
import { fetchOnaNodeDetails, fetchSubgraph } from '../api/ona';
import { riskLevelColor } from '../mock/mockData';
import { buildSubgraphMock } from '../mock/subgraphMock';
import { EMPLOYEE_REGISTRY, SHEN_HASH, LIXIA_HASH } from '../mock/employeeRegistry';

const ONAPrototype = ({ onNavigateToDrillDown }) => {
  const containerRef = useRef(null);
  const graphRef = useRef(null);
  const destroyedRef = useRef(false);
  const [tooltipData, setTooltipData] = useState(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });
  const [showTooltip, setShowTooltip] = useState(false);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [totalLoss, setTotalLoss] = useState(284500);
  const [filterLevel, setFilterLevel] = useState('all');
  const [searchValue, setSearchValue] = useState('');
  const [subgraphLoading, setSubgraphLoading] = useState(false);
  const [viewMode, setViewMode] = useState('global');
  const [graphLoaded, setGraphLoaded] = useState(false);
  // 九宫格数据 — 统一注册表派生
  const [gridData] = useState(() =>
    Object.values(EMPLOYEE_REGISTRY).map(e => ({
      label: e.name,
      riskLevel: e.riskLevel,
      perf: e.performanceScore,
      dept: e.department,
    }))
  );

  // 响应式统计 — 从 EMPLOYEE_REGISTRY 推导
  const [stats, setStats] = useState(() => {
    const entries = Object.values(EMPLOYEE_REGISTRY);
    const redCount = entries.filter(e => e.riskLevel === 'HIGH').length;
    const orangeCount = entries.filter(e => e.riskLevel === 'MID').length;
    const loss = entries.reduce((sum, e) => sum + Math.round(e.originalRisk * e.monthlyIncome * 6), 0);
    return { redCount, orangeCount, totalEmployees: entries.length, totalLoss: loss };
  });

  const { redCount, orangeCount, totalEmployees } = stats;

  // 防抖悬停请求
  const fetchNodeDetailsWithDelay = useCallback(
    debounce(async (nodeId, x, y) => {
      try {
        const resp = await fetchOnaNodeDetails(nodeId);
        setTooltipData(resp.data);
        setTooltipPos({ x: x + 20, y: y + 20 });
        setShowTooltip(true);
      } catch (err) {
        console.error('Fetch ONA details failed', err);
      }
    }, 200),
    []
  );

  // 加载子图
  const loadSubgraph = useCallback(async (centerId) => {
    setSubgraphLoading(true);
    setViewMode('ego');
    try {
      let data;
      try {
        const resp = await fetchSubgraph(centerId, 2);
        data = resp.data;
      } catch {
        data = buildSubgraphMock(centerId, 2);
      }
      if (graphRef.current && !destroyedRef.current) {
        graphRef.current.changeData(data);
        setTimeout(() => {
          if (graphRef.current && !destroyedRef.current) {
            graphRef.current.fitView([60, 60, 60, 60], { duration: 400 });
          }
        }, 100);
      }
    } catch (err) {
      console.error('Load subgraph failed', err);
    }
    setSubgraphLoading(false);
  }, []);

  // 返回全局图
  const loadGlobalGraph = useCallback(async () => {
    setViewMode('global');
    if (!graphRef.current || destroyedRef.current) return;
    try {
      const resp = await fetch('/api/v1/ona/graph/topology');
      const data = await resp.json();
      if (data?.data) {
        graphRef.current.changeData(data.data);
        setTimeout(() => {
          if (graphRef.current && !destroyedRef.current) {
            graphRef.current.fitView([60, 60, 60, 60], { duration: 400 });
          }
        }, 100);
      }
    } catch {
      // fallback
    }
  }, []);

  useEffect(() => {
    if (graphRef.current || !containerRef.current) return;
    destroyedRef.current = false;

    const container = containerRef.current;
    const width = container.scrollWidth || window.innerWidth;
    const height = container.scrollHeight || window.innerHeight;

    // ===== G6 生产级配置 =====
    const graph = new G6.Graph({
      container,
      width,
      height,
      fitView: true,
      fitViewPadding: [60, 60, 60, 60],
      animate: true,
      enabledStack: false,           // 关闭历史操作栈，释放高频交互内存
      modes: {
        default: ['drag-canvas', 'zoom-canvas', 'drag-node'],
      },
      layout: {
        type: 'gForce',
        preventOverlap: true,
        nodeSize: 30,
        linkDistance: 200,
        edgeStrength: 100,
        nodeStrength: 500,
        gravity: 5,
        damping: 0.8,
        minMovementChange: 0.1,     // 提高收敛阈值，阻止海量节点微幅震荡
      },
      defaultNode: {
        size: 28,
        style: {
          fill: '#5B8FF9',
          stroke: '#5B8FF9',
          lineWidth: 1,
          opacity: 1,
          cursor: 'pointer',
        },
        labelCfg: {
          style: { fill: '#c8c8d0', fontSize: 11 },
          position: 'bottom',
          offset: 6,
        },
      },
      defaultEdge: {
        style: {
          stroke: '#2a2a3a',
          lineWidth: 1.5,
          opacity: 0.6,
          endArrow: { path: G6.Arrow.triangle(4, 6), fill: '#2a2a3a' },
        },
      },
      nodeStateStyles: {
        inactive: { opacity: 0.08, labelCfg: { style: { opacity: 0.08 } } },
        active: { lineWidth: 3, shadowBlur: 15, shadowColor: '#FF4D4F' },
      },
      edgeStateStyles: {
        inactive: { opacity: 0.05, stroke: '#2a2a3a' },
        active: { stroke: '#FF4D4F', lineWidth: 3, opacity: 1 },
      },
    });

    graphRef.current = graph;

    // 异步加载真实拓扑数据 — 等 G6 完成布局计算后再注入数据
    setTimeout(async () => {
      try {
        if (destroyedRef.current || !graphRef.current) return;
        const resp = await fetch('http://localhost:8000/api/v1/ona/graph/topology');
        const json = await resp.json();
        if (json?.data?.nodes && !destroyedRef.current) {
          graphRef.current.data(json.data);
          graphRef.current.render();
          setGraphLoaded(true);
          setTimeout(() => {
            if (graphRef.current && !destroyedRef.current) {
              graphRef.current.fitView([60, 60, 60, 60]);
            }
          }, 600);
          return;
        }
      } catch (err) {
        console.warn('拓扑数据加载失败', err.message);
      }
      if (!destroyedRef.current) {
        graphRef.current.data({ nodes: [], edges: [] });
        graphRef.current.render();
        setGraphLoaded(true);
      }
    }, 200);

    // ===== Zoom 事件：缩放 < 0.6 时隐藏所有标签 =====
    graph.on('wheel', () => {
      const zoom = graph.getZoom();
      graph.getNodes().forEach((node) => {
        const model = node.getModel();
        if (zoom < 0.6 && model.customLabelShown !== false) {
          model.customLabelShown = false;
          graph.updateItem(node, { labelCfg: { style: { opacity: 0 } } });
        } else if (zoom >= 0.6 && model.customLabelShown !== true) {
          model.customLabelShown = true;
          graph.updateItem(node, { labelCfg: { style: { opacity: 1 } } });
        }
      });
    });

    // ===== 悬停事件 =====
    graph.on('node:mouseenter', (e) => {
      if (destroyedRef.current) return;
      const item = e.item;
      const model = item.getModel();
      setHoveredNode(model.id);

      graph.setAutoPaint(false);
      graph.getNodes().forEach((node) => {
        graph.clearItemStates(node);
        if (node !== item) graph.setItemState(node, 'inactive', true);
        else graph.setItemState(node, 'active', true);
      });
      graph.getEdges().forEach((edge) => {
        graph.clearItemStates(edge);
        const source = edge.getSource();
        const target = edge.getTarget();
        if (source === item || target === item) graph.setItemState(edge, 'active', true);
        else graph.setItemState(edge, 'inactive', true);
      });
      graph.setAutoPaint(true);
      graph.paint();

      const point = graph.getClientByPoint(model.x, model.y);
      fetchNodeDetailsWithDelay(model.id, point.x, point.y);
    });

    // ===== 移出事件 =====
    graph.on('node:mouseleave', () => {
      if (destroyedRef.current) return;
      fetchNodeDetailsWithDelay.cancel();
      setShowTooltip(false);
      setHoveredNode(null);

      graph.setAutoPaint(false);
      graph.getNodes().forEach((node) => graph.clearItemStates(node));
      graph.getEdges().forEach((edge) => {
        graph.clearItemStates(edge);
        edge.update({ style: { stroke: '#2a2a3a', lineWidth: 1.5, opacity: 0.6 } });
      });
      graph.setAutoPaint(true);
      graph.paint();
    });

    // ===== 点击 =====
    graph.on('node:click', (e) => {
      const model = e.item.getModel();
      if (onNavigateToDrillDown) onNavigateToDrillDown(model.id);
    });

    const handleResize = () => {
      if (graphRef.current && !destroyedRef.current) {
        const w = container.scrollWidth || window.innerWidth;
        const h = container.scrollHeight || window.innerHeight;
        graphRef.current.changeSize(w, h);
      }
    };
    window.addEventListener('resize', handleResize);

    setTimeout(() => {
      if (graphRef.current && !destroyedRef.current) graphRef.current.fitView([60, 60, 60, 60]);
    }, 600);

    return () => {
      destroyedRef.current = true;
      window.removeEventListener('resize', handleResize);
      fetchNodeDetailsWithDelay.cancel();
      if (graphRef.current) { graphRef.current.destroy(); graphRef.current = null; }
    };
  }, []);

  // 搜索提交
  const handleSearch = () => {
    const val = searchValue.trim();
    if (!val) return;
    // 直接用 id 或 label 前缀
    const allIds = [
      SHEN_HASH,
      LIXIA_HASH,
    ];
    // 按 ID 或 标签匹配
    const matched = allIds.find(id => id.startsWith(val) || id.includes(val));
    if (matched) loadSubgraph(matched);
    else if (graphRef.current) {
      const found = graphRef.current.findById(val);
      if (found) loadSubgraph(val);
    }
  };

  // 快速聚焦：申鹏程
  const focusOnShen = () => loadSubgraph(SHEN_HASH);

  return (
    <div style={{ width: '100vw', height: '100vh', position: 'relative', overflow: 'hidden', background: '#0f0f1a' }}>
      {/* ===== 顶部大屏损失滚动数字 ===== */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, zIndex: 15,
        background: 'linear-gradient(180deg, rgba(15,15,26,0.98) 0%, rgba(15,15,26,0.9) 70%, transparent 100%)',
        padding: '14px 24px 20px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 32,
        pointerEvents: 'none',
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 10, color: '#888', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 2 }}>高风险人才总期望替换损失</div>
          <div style={{ fontSize: 34, fontWeight: 800, color: '#FF4D4F', fontFamily: 'monospace', letterSpacing: 1, textShadow: '0 0 30px rgba(255,77,79,0.3)' }}>
            ¥{stats.totalLoss.toLocaleString()}
          </div>
        </div>
        <div style={{ width: 1, height: 36, background: 'rgba(255,255,255,0.08)' }} />
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 10, color: '#888', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 4 }}>预警概览</div>
          <div style={{ display: 'flex', gap: 16, fontSize: 12 }}>
            <span><span style={{ color: '#FF4D4F', fontWeight: 700 }}>{stats.redCount}</span> <span style={{ color: '#666' }}>高危</span></span>
            <span><span style={{ color: '#FA8C16', fontWeight: 700 }}>{stats.orangeCount}</span> <span style={{ color: '#666' }}>中危</span></span>
            <span><span style={{ color: '#888', fontWeight: 700 }}>{stats.totalEmployees}</span> <span style={{ color: '#666' }}>全员</span></span>
          </div>
        </div>
        <div style={{ width: 1, height: 36, background: 'rgba(255,255,255,0.08)' }} />
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 10, color: '#888', letterSpacing: 2, textTransform: 'uppercase', marginBottom: 4 }}>风险-绩效九宫格</div>
          <div style={{ display: 'flex', gap: 4 }}>
            {['低', '中', '高'].map((r, ri) => (
              <div key={ri} style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {['高', '中', '低'].map((p, pi) => {
                  const matched = gridData.find(g => {
                    const rIdx = g.riskLevel === 'HIGH' ? 2 : g.riskLevel === 'MID' ? 1 : 0;
                    const pIdx = g.perf >= 4.2 ? 0 : g.perf >= 3.8 ? 1 : 2;
                    return rIdx === ri && pIdx === pi;
                  });
                  const bg = !matched ? 'rgba(255,255,255,0.03)' :
                    matched.riskLevel === 'HIGH' ? 'rgba(255,77,79,0.25)' :
                    'rgba(250,140,22,0.15)';
                  return (
                    <div key={`${ri}-${pi}`} style={{
                      width: 28, height: 20, borderRadius: 3, background: bg,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: matched ? 8 : 7, color: matched ? '#eee' : '#333',
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                    }} title={matched ? `${matched.label} (${matched.dept})` : ''}>
                      {matched ? matched.label.slice(-2) : '·'}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 控制面板 */}
      <div style={{
        position: 'absolute', top: 84, left: 20, zIndex: 10,
        background: 'rgba(20,20,35,0.92)', backdropFilter: 'blur(12px)',
        border: '1px solid rgba(255,255,255,0.08)',
        borderRadius: 12, padding: '20px 24px',
        minWidth: 250, boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
      }}>
        <h3 style={{ margin: 0, fontSize: 14, fontWeight: 600, color: '#e0e0e0', letterSpacing: 1, textTransform: 'uppercase' }}>
          组织稳定度控制中心
        </h3>

        {/* 搜索框 */}
        <div style={{ marginTop: 12, display: 'flex', gap: 6 }}>
          <input
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="搜索员工工号..."
            style={{
              flex: 1, padding: '6px 10px', borderRadius: 6, border: '1px solid rgba(255,255,255,0.1)',
              background: 'rgba(255,255,255,0.04)', color: '#ccc', fontSize: 11, outline: 'none',
            }}
          />
          <button onClick={handleSearch}
            style={{ padding: '6px 10px', borderRadius: 6, border: 'none', background: '#1890FF22', color: '#1890FF', fontSize: 11, cursor: 'pointer' }}>
            定位
          </button>
        </div>

        {/* 视图切换 */}
        {viewMode === 'ego' && (
          <div style={{ marginTop: 8, display: 'flex', gap: 6 }}>
            <span style={{ fontSize: 10, color: '#52C41A', background: 'rgba(82,196,26,0.1)', padding: '2px 8px', borderRadius: 4 }}>子图模式</span>
            <button onClick={loadGlobalGraph}
              style={{ padding: '2px 8px', borderRadius: 4, border: '1px solid rgba(255,255,255,0.1)', background: 'transparent', color: '#888', fontSize: 10, cursor: 'pointer' }}>
              返回全局</button>
          </div>
        )}

        {/* 快速定位 */}
        <div style={{ marginTop: 10 }}>
          <div style={{ fontSize: 10, color: '#666', marginBottom: 6 }}>快速聚焦 · 高危枢纽</div>
          <button onClick={focusOnShen}
            style={{ width: '100%', padding: '6px 0', borderRadius: 6, border: '1px solid rgba(255,77,79,0.3)', background: 'rgba(255,77,79,0.06)', color: '#FF4D4F', fontSize: 11, cursor: 'pointer' }}>
            🔴 聚焦 申鹏程（组织核心影响力 0.96）
          </button>
        </div>

        {/* 风险筛选 */}
        <div style={{ marginTop: 10 }}>
          <div style={{ fontSize: 11, color: '#888', marginBottom: 6 }}>风险等级筛选</div>
          <div style={{ display: 'flex', gap: 6 }}>
            {[
              { key: 'all', label: '全部', color: '#5B8FF9' },
              { key: 'RED', label: '高危', color: '#FF4D4F' },
            ].map((opt) => (
              <button key={opt.key} onClick={() => setFilterLevel(opt.key)}
                style={{ padding: '4px 12px', borderRadius: 6, border: filterLevel === opt.key ? `1px solid ${opt.color}` : '1px solid rgba(255,255,255,0.1)', background: filterLevel === opt.key ? `${opt.color}22` : 'transparent', color: filterLevel === opt.key ? opt.color : '#888', fontSize: 11, cursor: 'pointer' }}>
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {/* 图例 */}
        <div style={{ marginTop: 12, paddingTop: 10, borderTop: '1px solid rgba(255,255,255,0.06)', fontSize: 11 }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#FF4D4F', display: 'inline-block' }} />
              <span style={{ color: '#aaa' }}>高流失风险</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#5B8FF9', display: 'inline-block' }} />
              <span style={{ color: '#aaa' }}>一般员工</span>
            </div>
          </div>
        </div>

        <div style={{ marginTop: 10, paddingTop: 10, borderTop: '1px solid rgba(255,255,255,0.06)', fontSize: 11, color: '#666', lineHeight: 1.6 }}>
          🖱 悬停节点查看详情<br />
          🔍 滚轮缩放 · 缩放{'{<}'}0.6 自动隐藏标签<br />
          {viewMode === 'ego' ? '📌 子图模式 (≤50节点)' : '🌐 全局模式'}
        </div>
      </div>

      {/* G6 画布 */}
      <div ref={containerRef} style={{ width: '100%', height: '100%' }} />

      {/* 加载遮罩 */}
      {subgraphLoading && (
        <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%,-50%)', background: 'rgba(0,0,0,0.7)', padding: '16px 24px', borderRadius: 8, color: '#aaa', fontSize: 13, zIndex: 50 }}>
          ⏳ 加载子图...
        </div>
      )}

      {/* 悬停弹窗 */}
      {showTooltip && tooltipData && (
        <HoverTooltip
          data={tooltipData}
          position={tooltipPos}
          onClose={() => setShowTooltip(false)}
          onStartIntervention={() => {
            if (tooltipData && onNavigateToDrillDown) {
              onNavigateToDrillDown(tooltipData.node_info.employee_id_hash);
            }
          }}
        />
      )}

      {/* 水印 */}
      <div style={{ position: 'absolute', bottom: 16, right: 20, zIndex: 5, fontSize: 10, color: 'rgba(255,255,255,0.06)', letterSpacing: 1, userSelect: 'none', pointerEvents: 'none' }}>
        员工离职风险预测与管理平台 · PRD V4.0
      </div>
    </div>
  );
};

// =========================================================================
// 悬停弹窗
// =========================================================================
const HoverTooltip = ({ data, position, onClose, onStartIntervention }) => {
  const { node_info, risk_metrics, shap_risk_factors, cascade_effect_prediction, matched_playbook } = data;
  const isRed = risk_metrics.final_risk_level === 'RED';
  const isOrange = risk_metrics.final_risk_level === 'ORANGE';
  const borderColor = riskLevelColor(risk_metrics.final_risk_level);

  return (
    <div style={{
      position: 'absolute', left: position.x, top: position.y, zIndex: 100, width: 340,
      background: 'rgba(22,22,36,0.96)', backdropFilter: 'blur(16px)',
      border: `1px solid rgba(255,255,255,0.1)`, borderTop: `4px solid ${borderColor}`,
      borderRadius: 12, padding: 0, overflow: 'hidden',
    }}>
      <div style={{ padding: '16px 18px 12px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ fontSize: 15, fontWeight: 600, color: '#f0f0f0' }}>{node_info.display_alias}</div>
          <div style={{ fontSize: 11, color: '#777', marginTop: 2 }}>
            {node_info.department}{node_info.job_level ? ` · ${node_info.job_level}` : ''}{node_info.tenure_years ? ` · ${node_info.tenure_years}年` : ''}
          </div>
        </div>
        <div style={{ padding: '3px 10px', borderRadius: 4, fontSize: 11, fontWeight: 600, background: isRed ? 'rgba(255,77,79,0.2)' : isOrange ? 'rgba(250,140,22,0.2)' : 'rgba(82,196,26,0.2)', color: isRed ? '#FF4D4F' : isOrange ? '#FA8C16' : '#52C41A', border: `1px solid ${borderColor}33` }}>
          {isRed ? '高危' : isOrange ? '中危' : '关注'}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 1, margin: '0 18px', borderRadius: 8, overflow: 'hidden' }}>
        {[
          { label: '离职概率', value: `${(risk_metrics.base_turnover_probability * 100).toFixed(0)}%`, color: isRed ? '#FF4D4F' : '#FFA940' },
          { label: '组织核心影响力', value: risk_metrics.ona_centrality_score.toFixed(2), color: '#5B8FF9' },
          { label: '骨干离职辐射圈', value: `Top ${((1 - risk_metrics.organization_shock_index) * 100).toFixed(0)}%`, color: '#FF4D4F' },
        ].map((item, i) => (
          <div key={i} style={{ textAlign: 'center', padding: '10px 4px', background: 'rgba(0,0,0,0.2)' }}>
            <div style={{ fontSize: 16, fontWeight: 700, color: item.color, fontFamily: 'monospace' }}>{item.value}</div>
            <div style={{ fontSize: 10, color: '#777', marginTop: 2 }}>{item.label}</div>
          </div>
        ))}
      </div>

      {shap_risk_factors.length > 0 && (
        <div style={{ padding: '0 18px 12px' }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: '#999', marginBottom: 8 }}>核心不满驱动因子</div>
          {shap_risk_factors.map((factor) => (
            <div key={factor.factor_name} style={{ marginBottom: 8 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginBottom: 3 }}>
                <span style={{ color: '#ccc' }}>{factor.factor_label}</span>
                <span style={{ color: '#888' }}>{factor.current_value}</span>
              </div>
              <div style={{ background: 'rgba(255,255,255,0.06)', height: 4, borderRadius: 2, overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${Math.min(factor.shap_value * 100, 100)}%`, background: 'linear-gradient(90deg, #FF4D4F, #FF7A45)', borderRadius: 2 }} />
              </div>
            </div>
          ))}
        </div>
      )}

      {cascade_effect_prediction.direct_impact_nodes_count > 0 && (
        <div style={{ padding: '0 18px 12px' }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: '#999', marginBottom: 6 }}>潜在团队流失放大效应 ⚠</div>
          <div style={{ fontSize: 11, color: '#aaa' }}>
            预计连带影响 <strong style={{ color: '#FF4D4F' }}>{cascade_effect_prediction.total_downstream_risks_count}</strong> 人
          </div>
          <div style={{ fontSize: 10, color: '#666', fontStyle: 'italic', marginTop: 1 }}>
            流失概率放大 {cascade_effect_prediction.co_leaver_risk_multiplier}x · 离职将引发关联震荡
          </div>
        </div>
      )}

      <div style={{ padding: '12px 18px', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
        <button onClick={onStartIntervention}
          style={{ width: '100%', padding: '10px 0', background: 'linear-gradient(135deg, #1890FF, #096DD9)', color: '#fff', border: 'none', borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: 'pointer', letterSpacing: 0.5 }}>
          查看详情与决策沙盘
        </button>
      </div>
    </div>
  );
};

export default ONAPrototype;
