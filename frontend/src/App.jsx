import { useState } from 'react'
import ONAPrototype from './components/OnaTopology.jsx'
import EmployeeDrillDown from './components/EmployeeDrillDown.jsx'

function App() {
  const [view, setView] = useState('topology') // 'topology' | 'drilldown'
  const [selectedEmployeeId, setSelectedEmployeeId] = useState(null)

  const handleNavigateToDrillDown = (employeeId) => {
    setSelectedEmployeeId(employeeId)
    setView('drilldown')
  }

  const handleBackToTopology = () => {
    setView('topology')
  }

  return (
    <div style={{ width: '100vw', height: '100vh', overflow: 'hidden' }}>
      {view === 'topology' ? (
        <div style={{
          width: '100%', height: '100%',
          transition: 'opacity 0.3s ease-out',
        }}>
          <ONAPrototype onNavigateToDrillDown={handleNavigateToDrillDown} />
        </div>
      ) : (
        <div style={{
          width: '100%', height: '100%',
          animation: 'slideIn 0.35s ease-out'
        }}>
          <EmployeeDrillDown
            employeeId={selectedEmployeeId}
            onBack={handleBackToTopology}
          />
        </div>
      )}

      {/* 内联 @keyframes */}
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(4px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes slideIn {
          from { opacity: 0; transform: translateX(20px); }
          to   { opacity: 1; transform: translateX(0); }
        }
        @keyframes pulse {
          0%   { transform: scale(1); }
          50%  { transform: scale(1.05); }
          100% { transform: scale(1); }
        }
        input[type='range']::-webkit-slider-thumb {
          -webkit-appearance: none;
          appearance: none;
          width: 18px;
          height: 18px;
          border-radius: 50%;
          background: #1890FF;
          cursor: pointer;
          border: 2px solid #0f0f1a;
          box-shadow: 0 0 8px rgba(24,144,255,0.4);
        }
        input[type='range']::-moz-range-thumb {
          width: 18px;
          height: 18px;
          border-radius: 50%;
          background: #1890FF;
          cursor: pointer;
          border: 2px solid #0f0f1a;
        }
      `}</style>
    </div>
  )
}

export default App
