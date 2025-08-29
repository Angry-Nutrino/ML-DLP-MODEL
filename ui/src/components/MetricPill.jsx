import React from 'react'

export default function MetricPill({ label, value }) {
  return (
    <div className="pill" title={String(value)}>
      <span className="kbd">{label}</span> <strong>{(value*100).toFixed(1)}%</strong>
    </div>
  )
}
