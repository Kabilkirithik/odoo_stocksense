import { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { api } from '../api'
import './DashboardChatbot.css'

function getSessionId() {
  const storageKey = 'stocksense_chat_session_id'
  let sessionId = sessionStorage.getItem(storageKey)

  if (!sessionId) {
    sessionId = globalThis.crypto?.randomUUID?.() || `session-${Date.now()}-${Math.random().toString(36).slice(2)}`
    sessionStorage.setItem(storageKey, sessionId)
  }

  return sessionId
}

function DashboardChatbot() {
  const [isOpen, setIsOpen] = useState(false)
  const [sessionId] = useState(getSessionId)
  const [messages, setMessages] = useState([])
  const [draft, setDraft] = useState('')
  const [pendingAction, setPendingAction] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  useEffect(() => {
    if (isOpen) inputRef.current?.focus()
  }, [isOpen])

  async function sendMessage(message, confirmedAction = null) {
    const trimmedMessage = message.trim()
    if (!trimmedMessage || isLoading) return

    setError('')
    setDraft('')
    setIsLoading(true)
    if (confirmedAction) setPendingAction(null)

    const history = messages
      .filter((item) => item.role === 'user' || item.role === 'assistant')
      .map(({ role, content }) => ({ role, content }))

    setMessages((current) => [...current, { id: crypto.randomUUID(), role: 'user', content: trimmedMessage }])

    try {
      const payload = {
        message: trimmedMessage,
        session_id: sessionId,
        history,
      }
      if (confirmedAction) payload.confirmed_action = confirmedAction

      const response = await api.post('/api/chat', payload)
      if (response?.status && response.status !== 'success') {
        throw new Error(response.reply || 'The assistant could not complete that request.')
      }

      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: response?.reply || 'The assistant returned an empty response.',
          actionsPerformed: response?.actions_performed || [],
          provider: response?.provider,
          model: response?.model,
        },
      ])
      setPendingAction(response?.pending_action || null)
    } catch (requestError) {
      if (confirmedAction) setPendingAction(confirmedAction)
      setError(requestError.message || 'Could not reach the chat service. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  function handleSubmit(event) {
    event.preventDefault()
    sendMessage(draft)
  }

  function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      sendMessage(draft)
    }
  }

  function cancelAction() {
    setPendingAction(null)
    setMessages((current) => [...current, {
      id: crypto.randomUUID(),
      role: 'notice',
      content: 'Action cancelled. No changes were made.',
    }])
  }

  return (
    <>
      {!isOpen && (
        <button
          className="chat-launcher"
          type="button"
          aria-label="Open StockSense assistant"
          aria-expanded={false}
          onClick={() => setIsOpen(true)}
        >
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 11.5a7.5 7.5 0 0 1-7.5 7.5 8 8 0 0 1-3.4-.76L4 20l1.76-4.4A7.5 7.5 0 1 1 20 11.5Z" /><path d="M8.5 11.5h.01m3.49 0h.01m3.49 0h.01" /></svg>
        </button>
      )}

      <aside className={`chat-drawer${isOpen ? ' chat-drawer-open' : ''}`} aria-hidden={!isOpen}>
        <header className="chat-header">
          <div className="chat-header-copy">
            <span className="chat-eyebrow">STOCKSENSE</span>
            <h2>Inventory assistant</h2>
            <p>Ask about stock, receipts, and operations</p>
          </div>
          <button className="chat-close" type="button" aria-label="Close assistant" onClick={() => setIsOpen(false)}>
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18" /></svg>
          </button>
        </header>

        <div className="chat-messages" aria-live="polite">
          {messages.length === 0 && (
            <div className="chat-welcome">
              <span className="chat-welcome-mark" aria-hidden="true">S</span>
              <h3>What can I help you find?</h3>
              <p>Ask for a stock overview or get help with an inventory task.</p>
              <button type="button" onClick={() => sendMessage('What is our current stock overview?')}>
                Current stock overview <span aria-hidden="true">↗</span>
              </button>
            </div>
          )}

          {messages.map((message) => (
            <article className={`chat-message chat-message-${message.role}`} key={message.id}>
              {message.role === 'assistant' && <span className="chat-avatar" aria-hidden="true">S</span>}
              <div className="chat-message-body">
                {message.role === 'assistant' ? (
                  <div className="chat-markdown">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
                  </div>
                ) : message.role === 'notice' ? (
                  <p>{message.content}</p>
                ) : (
                  <p>{message.content}</p>
                )}
                {message.actionsPerformed?.length > 0 && (
                  <div className="chat-action-result">
                    {message.actionsPerformed.map((action, index) => (
                      <span key={`${action.tool || action.summary || 'action'}-${index}`}>
                        Completed: {action.summary || action.tool || 'Inventory action'}
                      </span>
                    ))}
                  </div>
                )}
                {message.provider && (
                  <span className="chat-model">{message.provider}{message.model ? ` · ${message.model}` : ''}</span>
                )}
              </div>
            </article>
          ))}

          {pendingAction && (
            <section className="chat-confirmation" aria-label="Confirm inventory action">
              <span className="chat-confirmation-label">ACTION NEEDS APPROVAL</span>
              <p>{pendingAction.summary || 'The assistant prepared an inventory change.'}</p>
              <div className="chat-confirmation-buttons">
                <button type="button" className="chat-confirm" disabled={isLoading} onClick={() => sendMessage('Yes, confirmed', pendingAction)}>
                  Confirm action
                </button>
                <button type="button" className="chat-cancel" disabled={isLoading} onClick={cancelAction}>
                  Cancel
                </button>
              </div>
            </section>
          )}

          {isLoading && <div className="chat-typing"><span /><span /><span /> <span>Thinking</span></div>}
          {error && <p className="chat-error" role="alert">{error}</p>}
          <div ref={messagesEndRef} />
        </div>

        <form className="chat-composer" onSubmit={handleSubmit}>
          <textarea
            ref={inputRef}
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Message the assistant..."
            aria-label="Message the inventory assistant"
            rows={1}
            disabled={isLoading}
          />
          <button type="submit" aria-label="Send message" disabled={isLoading || !draft.trim()}>
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m4 4 16 8-16 8 3-8-3-8Zm3 8h13" /></svg>
          </button>
          <span className="chat-composer-hint">Enter to send · Shift+Enter for a new line</span>
        </form>
      </aside>
    </>
  )
}

export default DashboardChatbot