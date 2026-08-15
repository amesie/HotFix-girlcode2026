import { useState } from "react"
import LoginScreen from "./screens/LoginScreen"
import DashboardScreen from "./screens/DashboardScreen"
import ResultsScreen from "./screens/ResultsScreen"
import ChatbotScreen from "./screens/ChatbotScreen"

export type Screen = "login" | "dashboard" | "results" | "chatbot"

export default function App() {
  const [screen, setScreen] = useState<Screen>("login")
  const [chatOpen, setChatOpen] = useState(false)

  const navigate = (s: Screen) => setScreen(s)

  return (
    <div
      style={{
        width: 390,
        minHeight: 844,
        backgroundColor: "#FFFDF5",
        borderRadius: 44,
        overflow: "hidden",
        position: "relative",
        boxShadow: "0 32px 80px rgba(71,60,51,0.28), 0 0 0 10px #2a221c",
        fontFamily: "'Nunito', sans-serif",
      }}
    >
      {screen === "login" && <LoginScreen onLogin={() => navigate("dashboard")} />}
      {screen === "dashboard" && (
        <DashboardScreen
          onCheckID={() => navigate("results")}
          onOpenChat={() => setChatOpen(true)}
        />
      )}
      {screen === "results" && (
        <ResultsScreen onBack={() => navigate("dashboard")} onOpenChat={() => setChatOpen(true)} />
      )}

      {/* Chatbot overlay — appears on top of any screen except login */}
      {chatOpen && screen !== "login" && (
        <ChatbotScreen onClose={() => setChatOpen(false)} />
      )}

      {/* Secretary bird widget — visible on dashboard & results when chat is closed */}
      {!chatOpen && screen !== "login" && (
        <SecretaryBirdWidget onOpen={() => setChatOpen(true)} />
      )}
    </div>
  )
}

function SecretaryBirdWidget({ onOpen }: { onOpen: () => void }) {
  return (
    <button
      onClick={onOpen}
      style={{
        position: "absolute",
        bottom: 28,
        right: 20,
        background: "none",
        border: "none",
        cursor: "pointer",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 6,
        zIndex: 50,
      }}
    >
      {/* Speech bubble */}
      <div
        style={{
          backgroundColor: "#FFFDF5",
          border: "1.5px solid #FDA769",
          borderRadius: 10,
          padding: "4px 10px",
          fontSize: 11,
          fontWeight: 700,
          color: "#473C33",
          position: "relative",
          whiteSpace: "nowrap",
        }}
      >
        Need help?
        <span
          style={{
            position: "absolute",
            bottom: -7,
            left: "50%",
            transform: "translateX(-50%)",
            width: 0,
            height: 0,
            borderLeft: "6px solid transparent",
            borderRight: "6px solid transparent",
            borderTop: "7px solid #FFFDF5",
          }}
        />
        <span
          style={{
            position: "absolute",
            bottom: -9,
            left: "50%",
            transform: "translateX(-50%)",
            width: 0,
            height: 0,
            borderLeft: "7px solid transparent",
            borderRight: "7px solid transparent",
            borderTop: "8px solid #FDA769",
            zIndex: -1,
          }}
        />
      </div>

      {/* Bird on orange circle */}
      <div
        style={{
          width: 58,
          height: 58,
          borderRadius: "50%",
          backgroundColor: "#FDA769",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          boxShadow: "0 4px 16px rgba(253,167,105,0.5)",
        }}
      >
        <SecretaryBirdSVG />
      </div>
    </button>
  )
}

function SecretaryBirdSVG() {
  return (
    <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
      {/* Crest feathers (black, fanned) */}
      <line x1="18" y1="10" x2="13" y2="2" stroke="#2a221c" strokeWidth="1.8" strokeLinecap="round" />
      <line x1="18" y1="10" x2="15" y2="1.5" stroke="#2a221c" strokeWidth="1.8" strokeLinecap="round" />
      <line x1="18" y1="10" x2="18" y2="1" stroke="#2a221c" strokeWidth="1.8" strokeLinecap="round" />
      <line x1="18" y1="10" x2="21" y2="1.5" stroke="#2a221c" strokeWidth="1.8" strokeLinecap="round" />
      <line x1="18" y1="10" x2="23" y2="2" stroke="#2a221c" strokeWidth="1.8" strokeLinecap="round" />
      {/* Head (cream/white) */}
      <circle cx="18" cy="15" r="8" fill="#FFFDF5" />
      {/* Orange face mask */}
      <ellipse cx="18" cy="15" rx="5.5" ry="4" fill="#FDA769" />
      {/* Eye */}
      <circle cx="20" cy="14" r="1.2" fill="#473C33" />
      <circle cx="20.4" cy="13.6" r="0.4" fill="#FFFDF5" />
      {/* Beak (grey-blue, small hooked) */}
      <path d="M22.5 15.5 C24 15.5 24.5 16.5 23.5 17 L21.5 16.5 Z" fill="#8096a0" />
      {/* Body */}
      <ellipse cx="18" cy="26" rx="7" ry="6" fill="#FFFDF5" />
      {/* Wing hints */}
      <ellipse cx="12" cy="25" rx="3" ry="5" fill="#e8e4d0" transform="rotate(-10 12 25)" />
      <ellipse cx="24" cy="25" rx="3" ry="5" fill="#e8e4d0" transform="rotate(10 24 25)" />
    </svg>
  )
}
