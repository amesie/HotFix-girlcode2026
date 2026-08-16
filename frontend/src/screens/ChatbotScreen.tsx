import { useState, useRef, useEffect } from "react"
import { sendChatMessage, type ChatResponse } from "../api/client"

type Message = {
  from: "bot" | "user"
  text: string
}

const SUGGESTIONS = [
  { icon: "👶", label: "Register a birth" },
  { icon: "🪪", label: "Renew my ID" },
  { icon: "✈️", label: "Apply for a passport" },
]

function buildReplyMessages(data: ChatResponse): Message[] {
  const messages: Message[] = [{ from: "bot", text: data.reply }]

  if (data.documentsNeeded.length > 0) {
    messages.push({
      from: "bot",
      text: "Documents needed:\n" + data.documentsNeeded.map((d) => `• ${d}`).join("\n"),
    })
  }

  const costTimeLines: string[] = []
  if (data.estimatedCost) {
    costTimeLines.push(`Estimated cost: ${data.estimatedCost}`)
  }
  if (data.estimatedTime) {
    costTimeLines.push(`Estimated time: ${data.estimatedTime}`)
  }
  if (data.nearestBranch) {
    if (costTimeLines.length > 0) costTimeLines.push("")
    costTimeLines.push(
      `Nearest branch: ${data.nearestBranch.name}, ${data.nearestBranch.address} (${data.nearestBranch.distanceKm} km away)`,
    )
  }
  if (costTimeLines.length > 0) {
    messages.push({ from: "bot", text: costTimeLines.join("\n") })
  }

  return messages
}

export default function ChatbotScreen({ onClose }: { onClose: () => void }) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [typing, setTyping] = useState(false)
  const [suggestionUsed, setSuggestionUsed] = useState(false)
  // Tappable choices for the question currently on screen (e.g. which
  // service, which sub-case) — tapping one fills the input rather than
  // sending immediately, so the user can still edit/add detail first.
  const [activeOptions, setActiveOptions] = useState<string[]>([])
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  // One id for this chat session, generated once on open, sent on every
  // turn so the backend can track multi-turn conversation state per user
  // instead of guessing/sharing it.
  const conversationIdRef = useRef<string>(crypto.randomUUID())

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, typing, activeOptions])

  const sendMessage = async (text: string) => {
    if (!text.trim()) return
    const userMsg: Message = { from: "user", text }
    setMessages((prev) => [...prev, userMsg])
    setInput("")
    setSuggestionUsed(true)
    setActiveOptions([])
    setTyping(true)

    try {
      const data = await sendChatMessage(text, conversationIdRef.current)
      const replies = buildReplyMessages(data)

      let delay = 700
      replies.forEach((reply, i) => {
        setTimeout(() => {
          setMessages((prev) => [...prev, reply])
          if (i === replies.length - 1) {
            setTyping(false)
            setActiveOptions(data.options ?? [])
          }
        }, delay + i * 500)
      })
    } catch (err) {
      setTyping(false)
      setMessages((prev) => [
        ...prev,
        { from: "bot", text: err instanceof Error ? err.message : "Something went wrong. Please try again." },
      ])
    }
  }

  const fillFromOption = (label: string) => {
    setInput(label)
    inputRef.current?.focus()
  }

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        backgroundColor: "#FFFDF5",
        display: "flex",
        flexDirection: "column",
        zIndex: 100,
      }}
    >
      {/* Header */}
      <div
        style={{
          backgroundColor: "#FDA769",
          padding: "52px 24px 18px",
          display: "flex",
          alignItems: "center",
          gap: 14,
          flexShrink: 0,
        }}
      >
        <div
          style={{
            width: 40,
            height: 40,
            borderRadius: "50%",
            backgroundColor: "rgba(255,255,255,0.25)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <svg width="22" height="22" viewBox="0 0 36 36" fill="none">
            {/* Mini secretary bird */}
            <line x1="18" y1="10" x2="14" y2="3" stroke="#2a221c" strokeWidth="1.8" strokeLinecap="round" />
            <line x1="18" y1="10" x2="18" y2="2" stroke="#2a221c" strokeWidth="1.8" strokeLinecap="round" />
            <line x1="18" y1="10" x2="22" y2="3" stroke="#2a221c" strokeWidth="1.8" strokeLinecap="round" />
            <circle cx="18" cy="16" r="7" fill="#FFFDF5" />
            <ellipse cx="18" cy="16" rx="4.5" ry="3.5" fill="#FDA769" />
            <circle cx="19.5" cy="15" r="1" fill="#473C33" />
            <path d="M22 16.5 C23 16.5 23.5 17.5 22.5 18 L21 17.5 Z" fill="#8096a0" />
          </svg>
        </div>
        <div style={{ flex: 1 }}>
          <p style={{ margin: 0, fontSize: 11, fontWeight: 800, color: "rgba(74,37,16,0.7)", textTransform: "uppercase", letterSpacing: "0.08em" }}>
            Verifi Assistant
          </p>
          <h2 style={{ margin: 0, fontSize: 20, fontFamily: "'DM Serif Display', serif", color: "#4a2510" }}>
            Ask Verifi
          </h2>
        </div>
        <button
          onClick={onClose}
          style={{
            width: 36,
            height: 36,
            borderRadius: 10,
            backgroundColor: "rgba(74,37,16,0.12)",
            border: "none",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#4a2510" strokeWidth="2.5" strokeLinecap="round">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>

      {/* Messages area */}
      <div
        className="scrollable"
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "20px 20px 12px",
          display: "flex",
          flexDirection: "column",
          gap: 10,
        }}
      >
        {/* Greeting bubble */}
        <div style={{ display: "flex", gap: 10, alignItems: "flex-end" }}>
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: "50%",
              backgroundColor: "#FDA769",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            <span style={{ fontSize: 14 }}>🐦</span>
          </div>
          <div
            style={{
              backgroundColor: "#FDA769",
              borderRadius: "18px 18px 18px 4px",
              padding: "12px 16px",
              maxWidth: "78%",
            }}
          >
            <p style={{ margin: 0, fontSize: 14, color: "#4a2510", fontWeight: 600, lineHeight: 1.5 }}>
              Hi <strong>Naledi</strong>, what do you need help with today?
            </p>
          </div>
        </div>

        {/* Suggestion buttons */}
        {!suggestionUsed && (
          <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 4 }}>
            {SUGGESTIONS.map((s) => (
              <SuggestionButton key={s.label} icon={s.icon} label={s.label} onPress={() => sendMessage(s.label)} />
            ))}
          </div>
        )}

        {/* Conversation */}
        {messages.map((m, i) => (
          <div
            key={i}
            style={{
              display: "flex",
              justifyContent: m.from === "user" ? "flex-end" : "flex-start",
              gap: 10,
              alignItems: "flex-end",
            }}
          >
            {m.from === "bot" && (
              <div
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: "50%",
                  backgroundColor: "#FDA769",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0,
                }}
              >
                <span style={{ fontSize: 14 }}>🐦</span>
              </div>
            )}
            <div
              style={{
                backgroundColor: m.from === "user" ? "#ABC270" : "#F5F1E4",
                borderRadius:
                  m.from === "user"
                    ? "18px 18px 4px 18px"
                    : "18px 18px 18px 4px",
                padding: "12px 16px",
                maxWidth: "78%",
              }}
            >
              <p
                style={{
                  margin: 0,
                  fontSize: 14,
                  color: m.from === "user" ? "#2d3d18" : "#473C33",
                  fontWeight: 600,
                  lineHeight: 1.6,
                  whiteSpace: "pre-line",
                }}
              >
                {m.text}
              </p>
            </div>
          </div>
        ))}

        {/* Tappable options for the current question — fills the input, doesn't auto-send */}
        {!typing && activeOptions.length > 0 && (
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginLeft: 42, marginTop: 2 }}>
            {activeOptions.map((label) => (
              <OptionChip key={label} label={label} onPress={() => fillFromOption(label)} />
            ))}
          </div>
        )}

        {/* Typing indicator */}
        {typing && (
          <div style={{ display: "flex", gap: 10, alignItems: "flex-end" }}>
            <div
              style={{
                width: 32,
                height: 32,
                borderRadius: "50%",
                backgroundColor: "#FDA769",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <span style={{ fontSize: 14 }}>🐦</span>
            </div>
            <div
              style={{
                backgroundColor: "#F5F1E4",
                borderRadius: "18px 18px 18px 4px",
                padding: "14px 18px",
                display: "flex",
                gap: 5,
                alignItems: "center",
              }}
            >
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  style={{
                    width: 7,
                    height: 7,
                    borderRadius: "50%",
                    backgroundColor: "#8A7F6E",
                    animation: `bounce 1.2s ${i * 0.2}s ease-in-out infinite`,
                  }}
                />
              ))}
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div
        style={{
          padding: "12px 16px 28px",
          backgroundColor: "#FFFDF5",
          borderTop: "1.5px solid #F5F1E4",
          display: "flex",
          gap: 10,
          alignItems: "center",
          flexShrink: 0,
        }}
      >
        <div
          style={{
            flex: 1,
            backgroundColor: "#F5F1E4",
            borderRadius: 16,
            padding: "12px 16px",
            display: "flex",
            alignItems: "center",
          }}
        >
          <input
            ref={inputRef}
            type="text"
            placeholder="Or type your own question..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage(input)}
            style={{
              flex: 1,
              background: "none",
              border: "none",
              outline: "none",
              fontSize: 14,
              fontWeight: 600,
              color: "#473C33",
              fontFamily: "'Nunito', sans-serif",
            }}
          />
        </div>
        <button
          onClick={() => sendMessage(input)}
          disabled={!input.trim()}
          style={{
            width: 46,
            height: 46,
            borderRadius: 14,
            border: "none",
            backgroundColor: input.trim() ? "#ABC270" : "#C8C2B4",
            cursor: input.trim() ? "pointer" : "default",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            transition: "background-color 0.15s",
            flexShrink: 0,
          }}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke={input.trim() ? "#2d3d18" : "#8A7F6E"} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </div>

      <style>{`
        @keyframes bounce {
          0%, 80%, 100% { transform: translateY(0); }
          40% { transform: translateY(-6px); }
        }
      `}</style>
    </div>
  )
}

function OptionChip({ label, onPress }: { label: string; onPress: () => void }) {
  const [pressed, setPressed] = useState(false)
  return (
    <button
      onPointerDown={() => setPressed(true)}
      onPointerUp={() => { setPressed(false); onPress() }}
      onPointerLeave={() => setPressed(false)}
      style={{
        backgroundColor: pressed ? "#e8b450" : "#FDA769",
        border: "none",
        borderRadius: 999,
        padding: "8px 14px",
        cursor: "pointer",
        transition: "all 0.1s ease",
        transform: pressed ? "scale(0.96)" : "scale(1)",
      }}
    >
      <span style={{ fontSize: 13, fontWeight: 700, color: "#4a2510", fontFamily: "'Nunito', sans-serif" }}>
        {label}
      </span>
    </button>
  )
}

function SuggestionButton({
  icon,
  label,
  onPress,
}: {
  icon: string
  label: string
  onPress: () => void
}) {
  const [pressed, setPressed] = useState(false)
  return (
    <button
      onPointerDown={() => setPressed(true)}
      onPointerUp={() => { setPressed(false); onPress() }}
      onPointerLeave={() => setPressed(false)}
      style={{
        width: "100%",
        backgroundColor: pressed ? "#e8e4d2" : "#F5F1E4",
        border: "none",
        borderRadius: 14,
        padding: "13px 16px",
        display: "flex",
        alignItems: "center",
        gap: 12,
        cursor: "pointer",
        transition: "all 0.1s ease",
        transform: pressed ? "scale(0.98)" : "scale(1)",
      }}
    >
      <span style={{ fontSize: 18 }}>{icon}</span>
      <span style={{ fontSize: 14, fontWeight: 700, color: "#473C33", fontFamily: "'Nunito', sans-serif" }}>
        {label}
      </span>
      <svg style={{ marginLeft: "auto" }} width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#8A7F6E" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="9 18 15 12 9 6" />
      </svg>
    </button>
  )
}
