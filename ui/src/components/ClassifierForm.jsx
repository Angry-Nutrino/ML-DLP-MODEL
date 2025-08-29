import React, { useState } from 'react'

function fillExampleSensitive(setters) {
  const { setFrom, setTo, setSubject, setBody, setAttachments } = setters
  setFrom('alice@corp.com')
  setTo('finance@demo.local')
  setSubject('Q3 Salary Sheet (Confidential)')
  setBody('Team, attached are the confidential salary sheets for Q3. Please restrict sharing outside payroll.')
  setAttachments('q3_salaries.xlsx')
}

function fillExampleNormal(setters) {
  const { setFrom, setTo, setSubject, setBody, setAttachments } = setters
  setFrom('bob@partner.com')
  setTo('support@demo.local')
  setSubject('Inquiry about product availability')
  setBody('Hello team, could you confirm if the 24-port switch is in stock next week? Thanks.')
  setAttachments('')
}

export default function ClassifierForm({ onSubmit, loading }) {
  const [from, setFrom] = useState('demo@corp.com')
  const [to, setTo] = useState('finance@demo.local')
  const [subject, setSubject] = useState('(demo)')
  const [body, setBody] = useState('Paste or type the email body here...')
  const [attachments, setAttachments] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    const payload = {
      subject,
      body,
      headers: { From: from, To: to },
      attachments: attachments
        ? attachments.split(',').map(x => ({ filename: x.trim() })).filter(x => x.filename)
        : []
    }
    onSubmit(payload)
  }

  return (
    <form onSubmit={handleSubmit} className="grid">
      <div>
        <div className="label">From</div>
        <input className="input" value={from} onChange={e => setFrom(e.target.value)} placeholder="alice@corp.com" />
      </div>
      <div>
        <div className="label">To</div>
        <input className="input" value={to} onChange={e => setTo(e.target.value)} placeholder="finance@demo.local" />
      </div>
      <div>
        <div className="label">Subject</div>
        <input className="input" value={subject} onChange={e => setSubject(e.target.value)} placeholder="Subject" />
      </div>
      <div style={{ gridColumn: '1 / -1' }}>
        <div className="label">Body</div>
        <textarea className="textarea" value={body} onChange={e => setBody(e.target.value)} />
      </div>
      <div>
        <div className="label">Attachment filenames (comma-separated)</div>
        <input className="input" value={attachments} onChange={e => setAttachments(e.target.value)} placeholder="example.xlsx, data.csv" />
      </div>

      <div className="row" style={{ gridColumn: '1 / -1', justifyContent: 'space-between' }}>
        <div className="row">
          <button className="button" type="submit" disabled={loading}>
            {loading ? 'Classifying…' : 'Classify Email'}
          </button>
          <button className="button ghost" type="button" onClick={() => fillExampleSensitive({ setFrom, setTo, setSubject, setBody, setAttachments })}>
            Fill Sensitive Sample
          </button>
          <button className="button ghost" type="button" onClick={() => fillExampleNormal({ setFrom, setTo, setSubject, setBody, setAttachments })}>
            Fill Normal Sample
          </button>
        </div>
        <div className="muted">Header-only demo; attachments are metadata for now.</div>
      </div>
    </form>
  )
}
