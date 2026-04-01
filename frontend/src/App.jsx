import { useState } from 'react'
import './App.css'

const STATUS_MESSAGES = {
  idle: '',
  uploading: 'Uploading PDFs...',
  extracting: 'Extracting text & images from PDFs...',
  analyzing: 'AI is analyzing both reports...',
  building: 'Generating your DDR report...',
  done: 'Report ready!',
  error: 'Something went wrong.',
}

function App() {
  const [inspectionFile, setInspectionFile] = useState(null)
  const [thermalFile, setThermalFile] = useState(null)
  const [status, setStatus] = useState('idle')
  const [errorMessage, setErrorMessage] = useState('')
  const [downloadUrl, setDownloadUrl] = useState('')

  const handleGenerate = async () => {
    if (!inspectionFile || !thermalFile) return

    setStatus('uploading')
    setErrorMessage('')
    setDownloadUrl('')

    const formData = new FormData()
    formData.append('inspection_pdf', inspectionFile)
    formData.append('thermal_pdf', thermalFile)

    try {
      setStatus('analyzing')

      const response = await fetch('/api/generate-ddr', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || 'Server error')
      }

      setStatus('building')
      const data = await response.json()

      setDownloadUrl(data.download_url)
      setStatus('done')
    } catch (err) {
      setErrorMessage(err.message || 'An unexpected error occurred.')
      setStatus('error')
    }
  }

  const handleReset = () => {
    setInspectionFile(null)
    setThermalFile(null)
    setStatus('idle')
    setErrorMessage('')
    setDownloadUrl('')
  }

  const isProcessing = ['uploading', 'extracting', 'analyzing', 'building'].includes(status)

  return (
    <div className="app">
      <div className="background-glow" />

      <div className="container">
        <header className="header">
          <div className="logo">
            <span className="logo-icon">📊</span>
            <h1>DDR Report Generator</h1>
          </div>
          <p className="subtitle">
            Upload your Inspection & Thermal reports to generate a
            professional Detailed Diagnostic Report powered by AI.
          </p>
        </header>

        <div className="card">
          {status === 'idle' && (
            <>
              <div className="upload-grid">
                <UploadZone
                  label="Inspection Report"
                  icon="🔍"
                  file={inspectionFile}
                  onFileSelect={setInspectionFile}
                />
                <UploadZone
                  label="Thermal Report"
                  icon="🌡️"
                  file={thermalFile}
                  onFileSelect={setThermalFile}
                />
              </div>

              <button
                className="generate-btn"
                disabled={!inspectionFile || !thermalFile}
                onClick={handleGenerate}
              >
                <span className="btn-icon">⚡</span>
                Generate DDR Report
              </button>
            </>
          )}

          {isProcessing && (
            <div className="processing">
              <div className="spinner" />
              <p className="status-text">{STATUS_MESSAGES[status]}</p>
              <p className="status-sub">This may take a minute...</p>
            </div>
          )}

          {status === 'done' && (
            <div className="success">
              <div className="success-icon">✅</div>
              <h2>Report Generated Successfully!</h2>
              <p>Your Detailed Diagnostic Report is ready for download.</p>
              <a href={downloadUrl} className="download-btn" download>
                📥 Download DDR Report
              </a>
              <button className="reset-btn" onClick={handleReset}>
                Generate Another Report
              </button>
            </div>
          )}

          {status === 'error' && (
            <div className="error-state">
              <div className="error-icon">❌</div>
              <h2>Generation Failed</h2>
              <p className="error-msg">{errorMessage}</p>
              <button className="reset-btn" onClick={handleReset}>
                Try Again
              </button>
            </div>
          )}
        </div>

        <footer className="footer">
          <p>Powered by Groq AI &bull; Built with FastAPI & React</p>
        </footer>
      </div>
    </div>
  )
}

function UploadZone({ label, icon, file, onFileSelect }) {
  const [isDragging, setIsDragging] = useState(false)

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)
    const dropped = e.dataTransfer.files[0]
    if (dropped && dropped.name.toLowerCase().endsWith('.pdf')) {
      onFileSelect(dropped)
    }
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    setIsDragging(true)
  }

  return (
    <label
      className={`upload-zone ${isDragging ? 'dragging' : ''} ${file ? 'has-file' : ''}`}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={() => setIsDragging(false)}
    >
      <input
        type="file"
        accept=".pdf"
        hidden
        onChange={(e) => onFileSelect(e.target.files[0])}
      />
      <span className="upload-icon">{icon}</span>
      <span className="upload-label">{label}</span>
      {file ? (
        <span className="file-name">✓ {file.name}</span>
      ) : (
        <span className="upload-hint">Drag & drop or click to browse</span>
      )}
    </label>
  )
}

export default App
