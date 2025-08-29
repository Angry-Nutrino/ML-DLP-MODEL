import React, { useState } from 'react'
import ClassifierForm from './components/ClassifierForm.jsx'
import ResultCard from './components/ResultCard.jsx'

export default function App() {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  async function classify(payload) {
    setLoading(true)
    setResult(null)
    try {
      const res = await fetch('/api/classify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': 'DEMO_KEY'
        },
        body: JSON.stringify(payload)
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setResult(data)
    } catch (e) {
      setResult({ error: e.message })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <div className="card">
        <div className="header">
          <div className="title">DLP Email Classifier</div>
          <div className="badge">Demo • SMTP ⇄ FastAPI ⇄ React</div>
        </div>
        <ClassifierForm onSubmit={classify} loading={loading} />
        <ResultCard result={result} />
      </div>
      <footer>UI proxies <span className="kbd">/api</span> → FastAPI • MailHog at <span className="kbd">localhost:8025</span></footer>
    </div>
  )
}
