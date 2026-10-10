import React, { useState } from 'react'

interface QuestionFormProps {
  onSubmit: (question: string, context?: string) => void
  isLoading: boolean
}

export const QuestionForm: React.FC<QuestionFormProps> = ({ onSubmit, isLoading }) => {
  const [question, setQuestion] = useState('')
  const [context, setContext] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!question.trim()) return
    onSubmit(question.trim(), context.trim() ? context.trim() : undefined)
  }

  const clearQuestion = () => setQuestion('')
  const clearContext = () => setContext('')

  return (
    <div className="question-form-container">
      <div className="hero-section">
        <h2 className="hero-title">The answer is out there. Get moving.</h2>
        <p className="hero-subtitle">
          Ask normally. Tell us where you are or plan to go if it matters.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="question-form">
        <div className="form-group">
          <div className="form-label-row">
            <label htmlFor="question-input" className="form-label">
              What do you want to do or find out nearby?
            </label>
            <span className={`char-counter ${question.length >= 280 ? 'warn' : ''}`}>
              {question.length}/300
            </span>
          </div>
          <div className="input-wrapper">
            <textarea
              id="question-input"
              className="form-textarea"
              placeholder="e.g. How do I join a casual pickup game at the court?"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              disabled={isLoading}
              required
              maxLength={300}
              rows={3}
            />
            {question.length > 0 && (
              <button
                type="button"
                className="input-clear-btn"
                onClick={clearQuestion}
                aria-label="Clear question"
              >
                ✕
              </button>
            )}
          </div>
        </div>

        <div className="form-group">
          <div className="form-label-row">
            <label htmlFor="context-input" className="form-label">
              Area or place <span className="form-label-subtle">(optional context)</span>
            </label>
            <span className="char-counter">{context.length}/200</span>
          </div>
          <div className="input-wrapper">
            <input
              id="context-input"
              type="text"
              className="form-input"
              placeholder="e.g. Campus sports court, downtown market..."
              value={context}
              onChange={(e) => setContext(e.target.value)}
              disabled={isLoading}
              maxLength={200}
            />
            {context.length > 0 && (
              <button
                type="button"
                className="input-clear-btn"
                onClick={clearContext}
                aria-label="Clear context"
              >
                ✕
              </button>
            )}
          </div>
        </div>

        <div className="privacy-badge-banner">
          <span className="privacy-icon">🛡️</span>
          <span>No GPS tracking • Pure local intention • Off the screen</span>
        </div>

        <button type="submit" className="submit-btn" disabled={isLoading || !question.trim()}>
          {isLoading ? (
            <span className="btn-loading-content">
              <span className="spinner-inline" /> Routing intention...
            </span>
          ) : (
            <span>Find physical step →</span>
          )}
        </button>
      </form>
    </div>
  )
}
