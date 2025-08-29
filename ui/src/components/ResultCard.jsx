import React from 'react'

function actionClass(action) {
  if (action === 'Send Normally') return 'success'
  if (action === 'Quarantine for Review') return 'warn'
  return 'danger'
}

export default function ResultCard({ result }) {
  if (!result) return null
  if (result.error) return <div className="result"><div className="pill danger">Error</div><div style={{marginTop:8}}>{result.error}</div></div>

  const sensitiveScore = typeof result.score === 'number' ? result.score : 0
  return (
    <div className="result">
      <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:8}}>
        <div className={`pill ${actionClass(result.action)}`}>{result.action}</div>
        <div className="muted">Label: <span className="kbd">{result.label}</span></div>
      </div>
      <div className="progress" aria-label="Sensitive Probability">
        <div style={{ width: `${Math.round(sensitiveScore*100)}%` }} />
      </div>
      <div style={{display:'flex', gap:8, flexWrap:'wrap', marginTop:8}}>
        {Object.entries(result.scores || {}).map(([k,v]) => (
          <div key={k} className="pill" style={{background:'#0b1426', border:'1px solid #23365a'}}>
            <span className="kbd">{k}</span> <strong>{(v*100).toFixed(1)}%</strong>
          </div>
        ))}
      </div>
      {result.rationale?.length ? (
        <div style={{marginTop:10}} className="muted">
          Rationale: {result.rationale.join(', ')}
        </div>
      ) : null}
    </div>
  )
}
