import { useState } from "react"

const PIN_LENGTH = 5

export default function LoginScreen({ onLogin }: { onLogin: () => void }) {
  const [pin, setPin] = useState("")
  const [shake, setShake] = useState(false)

  const handleDigit = (d: string) => {
    if (pin.length >= PIN_LENGTH) return
    const next = pin + d
    setPin(next)
    if (next.length === PIN_LENGTH) {
      // Simulate auth — any PIN works
      setTimeout(onLogin, 300)
    }
  }

  const handleBack = () => setPin((p) => p.slice(0, -1))

  return (
    <div
      style={{
        minHeight: 844,
        backgroundColor: "#FFFDF5",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "0 32px 40px",
        gap: 0,
      }}
    >
      {/* Shield icon */}
      <div style={{ marginBottom: 20 }}>
        <ShieldIcon />
      </div>

      {/* Heading */}
      <h1
        style={{
          fontFamily: "'DM Serif Display', serif",
          fontSize: 30,
          color: "#473C33",
          margin: 0,
          textAlign: "center",
          lineHeight: 1.2,
        }}
      >
        Welcome to Verifi
      </h1>
      <p
        style={{
          fontSize: 15,
          color: "#8A7F6E",
          margin: "8px 0 40px",
          textAlign: "center",
          fontWeight: 500,
        }}
      >
        Log in with your PIN
      </p>

      {/* PIN dots */}
      <div
        style={{
          display: "flex",
          gap: 14,
          marginBottom: 48,
          animation: shake ? "shake 0.3s ease" : "none",
        }}
      >
        {Array.from({ length: PIN_LENGTH }).map((_, i) => (
          <div
            key={i}
            style={{
              width: 18,
              height: 18,
              borderRadius: "50%",
              border: `2px solid ${i < pin.length ? "#ABC270" : "#C8C2B4"}`,
              backgroundColor: i < pin.length ? "#ABC270" : "transparent",
              transition: "all 0.15s ease",
              transform: i < pin.length ? "scale(1.1)" : "scale(1)",
            }}
          />
        ))}
      </div>

      {/* Keypad */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 72px)",
          gap: 14,
        }}
      >
        {["1","2","3","4","5","6","7","8","9"].map((d) => (
          <KeypadButton key={d} label={d} onPress={() => handleDigit(d)} />
        ))}
        {/* Help */}
        <KeypadButton
          label="?"
          onPress={() => {}}
          style={{ backgroundColor: "#F5F1E4", color: "#8A7F6E" }}
        />
        <KeypadButton label="0" onPress={() => handleDigit("0")} />
        {/* Backspace */}
        <KeypadButton
          label="⌫"
          onPress={handleBack}
          style={{ backgroundColor: "#F5F1E4", color: "#8A7F6E" }}
        />
      </div>

      <p style={{ fontSize: 12, color: "#8A7F6E", marginTop: 32, textAlign: "center" }}>
        Forgot your PIN?{" "}
        <span style={{ color: "#ABC270", fontWeight: 700, cursor: "pointer" }}>Get help</span>
      </p>
    </div>
  )
}

function KeypadButton({
  label,
  onPress,
  style,
}: {
  label: string
  onPress: () => void
  style?: React.CSSProperties
}) {
  const [pressed, setPressed] = useState(false)
  return (
    <button
      onPointerDown={() => setPressed(true)}
      onPointerUp={() => { setPressed(false); onPress() }}
      onPointerLeave={() => setPressed(false)}
      style={{
        width: 72,
        height: 72,
        borderRadius: 20,
        border: "none",
        backgroundColor: pressed ? "#e0dccc" : "#F5F1E4",
        color: "#473C33",
        fontSize: label === "⌫" ? 20 : 24,
        fontWeight: 700,
        fontFamily: "'Nunito', sans-serif",
        cursor: "pointer",
        transition: "all 0.1s ease",
        transform: pressed ? "scale(0.94)" : "scale(1)",
        boxShadow: pressed ? "none" : "0 2px 6px rgba(71,60,51,0.1)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        ...style,
      }}
    >
      {label}
    </button>
  )
}

function ShieldIcon() {
  return (
    <div
      style={{
        width: 80,
        height: 80,
        borderRadius: 24,
        backgroundColor: "#ABC270",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        boxShadow: "0 8px 24px rgba(171,194,112,0.4)",
      }}
    >
      <svg width="44" height="44" viewBox="0 0 44 44" fill="none">
        <path
          d="M22 4L8 10v10c0 9 6 17.4 14 20 8-2.6 14-11 14-20V10L22 4z"
          fill="#FFFDF5"
          stroke="#FFFDF5"
          strokeWidth="1.5"
          strokeLinejoin="round"
        />
        <path
          d="M15 22l5 5 9-9"
          stroke="#ABC270"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </div>
  )
}
