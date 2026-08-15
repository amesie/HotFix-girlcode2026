import { useState } from "react"
import { checkIdentity, type CheckIdentityResponse } from "../api/client"

type Step = "input" | "results"

export default function ResultsScreen({
  onBack,
  onOpenChat,
}: {
  onBack: () => void
  onOpenChat: () => void
}) {
  const [step, setStep] = useState<Step>("input")
  const [idNumber, setIdNumber] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<CheckIdentityResponse | null>(null)

  const handleCheck = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await checkIdentity(idNumber)
      setResult(data)
      setStep("results")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className="scrollable"
      style={{
        minHeight: 844,
        backgroundColor: "#FFFDF5",
        display: "flex",
        flexDirection: "column",
        overflowY: "auto",
      }}
    >
      {/* Status bar space */}
      <div style={{ height: 48 }} />

      {/* Header */}
      <div
        style={{
          padding: "0 24px 20px",
          display: "flex",
          alignItems: "center",
          gap: 14,
        }}
      >
        <button
          onClick={onBack}
          style={{
            width: 40,
            height: 40,
            borderRadius: 12,
            backgroundColor: "#F5F1E4",
            border: "none",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#473C33" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="15 18 9 12 15 6" />
          </svg>
        </button>
        <h1
          style={{
            margin: 0,
            fontSize: 22,
            fontFamily: "'DM Serif Display', serif",
            color: "#473C33",
          }}
        >
          {step === "input" ? "Check my ID record" : "Your results"}
        </h1>
      </div>

      {step === "input" ? (
        <InputStep
          idNumber={idNumber}
          setIdNumber={setIdNumber}
          onCheck={handleCheck}
          loading={loading}
          error={error}
        />
      ) : (
        result && <ResultsStep result={result} onChat={onOpenChat} />
      )}

      <div style={{ height: 100 }} />
    </div>
  )
}

function InputStep({
  idNumber,
  setIdNumber,
  onCheck,
  loading,
  error,
}: {
  idNumber: string
  setIdNumber: (v: string) => void
  onCheck: () => void
  loading: boolean
  error: string | null
}) {
  return (
    <div style={{ padding: "0 24px", display: "flex", flexDirection: "column", gap: 16 }}>
      <p style={{ margin: 0, fontSize: 15, color: "#8A7F6E", fontWeight: 600 }}>
        Enter your 13-digit South African ID number to check your record.
      </p>

      <div
        style={{
          backgroundColor: "#F5F1E4",
          borderRadius: 18,
          padding: "14px 18px",
          display: "flex",
          alignItems: "center",
          gap: 12,
          border: `2px solid ${error ? "#FDA769" : "transparent"}`,
          transition: "border-color 0.15s",
        }}
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#8A7F6E" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <rect x="3" y="4" width="18" height="16" rx="2" />
          <line x1="7" y1="9" x2="17" y2="9" />
          <line x1="7" y1="13" x2="13" y2="13" />
        </svg>
        <input
          type="tel"
          inputMode="numeric"
          placeholder="8501015800081"
          value={idNumber}
          onChange={(e) => setIdNumber(e.target.value.replace(/\D/g, "").slice(0, 13))}
          style={{
            flex: 1,
            background: "none",
            border: "none",
            outline: "none",
            fontSize: 17,
            fontWeight: 700,
            color: "#473C33",
            fontFamily: "'Nunito', sans-serif",
            letterSpacing: "0.04em",
          }}
        />
        {idNumber.length === 13 && (
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ABC270" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="20 6 9 17 4 12" />
          </svg>
        )}
      </div>

      {error ? (
        <p style={{ margin: 0, fontSize: 12, color: "#4a2510", fontWeight: 700 }}>{error}</p>
      ) : (
        <p style={{ margin: 0, fontSize: 12, color: "#8A7F6E", fontWeight: 600 }}>
          Your ID number is only used to check records. It is never stored.
        </p>
      )}

      <button
        onClick={onCheck}
        disabled={idNumber.length !== 13 || loading}
        style={{
          width: "100%",
          padding: "18px",
          borderRadius: 18,
          border: "none",
          backgroundColor: idNumber.length === 13 ? "#ABC270" : "#C8C2B4",
          color: idNumber.length === 13 ? "#2d3d18" : "#8A7F6E",
          fontSize: 16,
          fontWeight: 800,
          fontFamily: "'Nunito', sans-serif",
          cursor: idNumber.length === 13 ? "pointer" : "default",
          transition: "all 0.15s ease",
          boxShadow: idNumber.length === 13 ? "0 6px 20px rgba(171,194,112,0.4)" : "none",
        }}
      >
        {loading ? "Checking…" : "Check my record →"}
      </button>
    </div>
  )
}

function ResultsStep({ result, onChat }: { result: CheckIdentityResponse; onChat: () => void }) {
  const [callPressed, setCallPressed] = useState(false)

  if (!result.found) {
    return (
      <div style={{ padding: "0 24px", display: "flex", flexDirection: "column", gap: 14 }}>
        <NotFoundCard message={result.message ?? "No record found for this ID number in our demo dataset."} />
        <button
          onClick={onChat}
          style={{
            width: "100%",
            padding: "16px",
            borderRadius: 18,
            border: "2px solid #F5F1E4",
            backgroundColor: "transparent",
            color: "#8A7F6E",
            fontSize: 15,
            fontWeight: 700,
            fontFamily: "'Nunito', sans-serif",
            cursor: "pointer",
          }}
        >
          Ask Verifi for more help
        </button>
      </div>
    )
  }

  const activeFlags = result.flags.filter((f) => f.type !== "no_flags")
  const cleanFlags = result.flags.filter((f) => f.type === "no_flags")
  const nextSteps = Array.from(new Set(activeFlags.flatMap((f) => f.nextSteps)))

  return (
    <div style={{ padding: "0 24px", display: "flex", flexDirection: "column", gap: 14 }}>
      <p
        style={{
          margin: 0,
          fontSize: 15,
          color: "#473C33",
          fontWeight: 600,
          lineHeight: 1.5,
        }}
      >
        Hi <strong>Thabo</strong>, here's what we found:
      </p>

      {activeFlags.map((flag, i) => (
        <FlagCard key={i} title={flag.title} text={flag.plainExplanation} />
      ))}

      {cleanFlags.map((flag, i) => (
        <CleanCard key={i} title={flag.title} subtitle={flag.plainExplanation} />
      ))}

      {nextSteps.length > 0 && (
        <div
          style={{
            backgroundColor: "#F5F1E4",
            borderRadius: 22,
            padding: "20px 20px",
          }}
        >
          <h3
            style={{
              margin: "0 0 14px",
              fontSize: 16,
              fontFamily: "'DM Serif Display', serif",
              color: "#473C33",
            }}
          >
            What to do next
          </h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {nextSteps.map((text, i) => (
              <Step key={i} n={i + 1} text={text} />
            ))}
          </div>
        </div>
      )}

      {activeFlags.length > 0 && (
        <button
          onPointerDown={() => setCallPressed(true)}
          onPointerUp={() => setCallPressed(false)}
          onPointerLeave={() => setCallPressed(false)}
          style={{
            width: "100%",
            padding: "18px",
            borderRadius: 18,
            border: "none",
            backgroundColor: "#ABC270",
            color: "#2d3d18",
            fontSize: 16,
            fontWeight: 800,
            fontFamily: "'Nunito', sans-serif",
            cursor: "pointer",
            boxShadow: callPressed ? "none" : "0 6px 20px rgba(171,194,112,0.4)",
            transform: callPressed ? "scale(0.97)" : "scale(1)",
            transition: "all 0.15s ease",
          }}
        >
          Call the fraud line now →
        </button>
      )}

      <button
        onClick={onChat}
        style={{
          width: "100%",
          padding: "16px",
          borderRadius: 18,
          border: "2px solid #F5F1E4",
          backgroundColor: "transparent",
          color: "#8A7F6E",
          fontSize: 15,
          fontWeight: 700,
          fontFamily: "'Nunito', sans-serif",
          cursor: "pointer",
        }}
      >
        Ask Verifi for more help
      </button>
    </div>
  )
}

function FlagCard({ title, text }: { title: string; text: string }) {
  return (
    <div
      style={{
        backgroundColor: "#FDA769",
        borderRadius: 22,
        padding: "20px 20px 18px",
        boxShadow: "0 6px 20px rgba(253,167,105,0.3)",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
        <div
          style={{
            width: 40,
            height: 40,
            borderRadius: 12,
            backgroundColor: "rgba(74,37,16,0.15)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
          }}
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#4a2510" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
        </div>
        <div>
          <p style={{ margin: 0, fontSize: 11, fontWeight: 800, color: "#4a2510", textTransform: "uppercase", letterSpacing: "0.08em" }}>
            Flag found
          </p>
          <p style={{ margin: 0, fontSize: 16, fontFamily: "'DM Serif Display', serif", color: "#4a2510" }}>
            {title}
          </p>
        </div>
      </div>
      <p
        style={{
          margin: 0,
          fontSize: 14,
          color: "#4a2510",
          lineHeight: 1.6,
          fontWeight: 600,
        }}
      >
        {text}
      </p>
    </div>
  )
}

function CleanCard({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div
      style={{
        backgroundColor: "#ABC270",
        borderRadius: 22,
        padding: "18px 20px",
        display: "flex",
        alignItems: "center",
        gap: 14,
        boxShadow: "0 6px 20px rgba(171,194,112,0.3)",
      }}
    >
      <div
        style={{
          width: 40,
          height: 40,
          borderRadius: 12,
          backgroundColor: "rgba(45,61,24,0.15)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
        }}
      >
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2d3d18" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="20 6 9 17 4 12" />
        </svg>
      </div>
      <div>
        <p style={{ margin: 0, fontSize: 14, fontWeight: 800, color: "#2d3d18" }}>{title}</p>
        <p style={{ margin: 0, fontSize: 12, color: "#2d3d18", opacity: 0.75, fontWeight: 600 }}>
          {subtitle}
        </p>
      </div>
    </div>
  )
}

function NotFoundCard({ message }: { message: string }) {
  return (
    <div
      style={{
        backgroundColor: "#F5F1E4",
        borderRadius: 22,
        padding: "20px 20px",
        display: "flex",
        alignItems: "center",
        gap: 14,
      }}
    >
      <div
        style={{
          width: 40,
          height: 40,
          borderRadius: 12,
          backgroundColor: "rgba(71,60,51,0.1)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
          fontSize: 18,
          fontWeight: 800,
          color: "#8A7F6E",
        }}
      >
        ?
      </div>
      <div>
        <p style={{ margin: 0, fontSize: 14, fontWeight: 800, color: "#473C33" }}>No record found</p>
        <p style={{ margin: 0, fontSize: 12, color: "#8A7F6E", opacity: 0.9, fontWeight: 600, lineHeight: 1.5 }}>
          {message}
        </p>
      </div>
    </div>
  )
}

function Step({ n, text }: { n: number; text: string }) {
  return (
    <div style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
      <div
        style={{
          width: 26,
          height: 26,
          borderRadius: 8,
          backgroundColor: "#ABC270",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
          fontSize: 13,
          fontWeight: 800,
          color: "#2d3d18",
          marginTop: 1,
        }}
      >
        {n}
      </div>
      <p style={{ margin: 0, fontSize: 14, color: "#473C33", fontWeight: 600, lineHeight: 1.5 }}>
        {text}
      </p>
    </div>
  )
}
