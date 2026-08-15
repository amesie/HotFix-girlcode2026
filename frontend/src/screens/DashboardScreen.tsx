import { useState } from "react"

export default function DashboardScreen({
  onCheckID,
  onOpenChat,
}: {
  onCheckID: () => void
  onOpenChat: () => void
}) {
  const [callPressed, setCallPressed] = useState(false)

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
      {/* Status bar */}
      <div
        style={{
          height: 48,
          backgroundColor: "#FFFDF5",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0 24px",
        }}
      >
        <span style={{ fontSize: 13, fontWeight: 700, color: "#473C33" }}>9:41</span>
        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
          <svg width="16" height="12" viewBox="0 0 16 12" fill="#473C33">
            <rect x="0" y="5" width="3" height="7" rx="1" />
            <rect x="4.5" y="3" width="3" height="9" rx="1" />
            <rect x="9" y="1" width="3" height="11" rx="1" />
            <rect x="13.5" y="0" width="2.5" height="12" rx="1" opacity="0.3" />
          </svg>
          <svg width="16" height="12" viewBox="0 0 16 12" fill="#473C33">
            <path d="M8 2C5 2 2.3 3.5 0.5 6L2 7.5C3.3 5.8 5.5 4.5 8 4.5S12.7 5.8 14 7.5L15.5 6C13.7 3.5 11 2 8 2z" />
            <path d="M8 6c-1.7 0-3.2.8-4.2 2L5.2 9.5C5.9 8.6 6.9 8 8 8s2.1.6 2.8 1.5L12.2 8C11.2 6.8 9.7 6 8 6z" />
            <circle cx="8" cy="11" r="1.5" />
          </svg>
          <svg width="25" height="12" viewBox="0 0 25 12" fill="none">
            <rect x="0.5" y="0.5" width="21" height="11" rx="3.5" stroke="#473C33" strokeOpacity="0.35" />
            <rect x="2" y="2" width="17" height="8" rx="2" fill="#473C33" />
            <path d="M23 4.5v3a1.5 1.5 0 000-3z" fill="#473C33" fillOpacity="0.4" />
          </svg>
        </div>
      </div>

      {/* Header */}
      <div
        style={{
          padding: "16px 24px 0",
          display: "flex",
          alignItems: "center",
          gap: 14,
        }}
      >
        <div
          style={{
            width: 52,
            height: 52,
            borderRadius: "50%",
            backgroundColor: "#FEC868",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 22,
            fontWeight: 800,
            color: "#473C33",
            flexShrink: 0,
            boxShadow: "0 4px 12px rgba(254,200,104,0.4)",
          }}
        >
          TM
        </div>
        <div>
          <p style={{ margin: 0, fontSize: 13, color: "#8A7F6E", fontWeight: 600 }}>
            Good morning
          </p>
          <h2
            style={{
              margin: 0,
              fontSize: 22,
              fontFamily: "'DM Serif Display', serif",
              color: "#473C33",
              lineHeight: 1.2,
            }}
          >
            Thabo Mokoena
          </h2>
        </div>
        <div style={{ marginLeft: "auto" }}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#8A7F6E" strokeWidth="2" strokeLinecap="round">
            <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9" />
            <path d="M13.73 21a2 2 0 01-3.46 0" />
          </svg>
        </div>
      </div>

      {/* ID Status pill */}
      <div style={{ padding: "16px 24px 0" }}>
        <div
          style={{
            backgroundColor: "#F5F1E4",
            borderRadius: 12,
            padding: "10px 16px",
            display: "flex",
            alignItems: "center",
            gap: 10,
          }}
        >
          <div
            style={{
              width: 8,
              height: 8,
              borderRadius: "50%",
              backgroundColor: "#ABC270",
              flexShrink: 0,
            }}
          />
          <span style={{ fontSize: 13, color: "#8A7F6E", fontWeight: 600 }}>
            ID: 8501015800081 · Last checked{" "}
          </span>
          <span style={{ fontSize: 13, color: "#473C33", fontWeight: 700 }}>3 days ago</span>
        </div>
      </div>

      {/* Action cards */}
      <div style={{ padding: "20px 24px 0", display: "flex", flexDirection: "column", gap: 14 }}>
        {/* Card 1 — Sage green */}
        <ActionCard
          color="#ABC270"
          textColor="#2d3d18"
          icon={<ShieldCardIcon />}
          title="Check my ID record"
          subtitle="See if anything looks wrong"
          linkLabel="Check"
          onPress={onCheckID}
        />

        {/* Card 2 — Soft orange */}
        <ActionCard
          color="#FDA769"
          textColor="#4a2510"
          icon={<ChatCardIcon />}
          title="Ask what I need to do"
          subtitle="Documents, cost, nearest branch"
          linkLabel="Ask"
          onPress={onOpenChat}
        />
      </div>

      {/* Info banner */}
      <div style={{ padding: "14px 24px 0" }}>
        <button
          onPointerDown={() => setCallPressed(true)}
          onPointerUp={() => setCallPressed(false)}
          onPointerLeave={() => setCallPressed(false)}
          style={{
            width: "100%",
            backgroundColor: callPressed ? "#e8b450" : "#FEC868",
            border: "none",
            borderRadius: 18,
            padding: "16px 20px",
            display: "flex",
            alignItems: "center",
            gap: 14,
            cursor: "pointer",
            transition: "all 0.15s ease",
            transform: callPressed ? "scale(0.98)" : "scale(1)",
          }}
        >
          <div
            style={{
              width: 40,
              height: 40,
              borderRadius: 12,
              backgroundColor: "rgba(71,60,51,0.12)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#473C33" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07A19.5 19.5 0 013.1 10.82 19.79 19.79 0 01.06 2.18 2 2 0 012.03 0h3a2 2 0 012 1.72c.127.96.361 1.903.7 2.81a2 2 0 01-.45 2.11L6.09 7.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0122 16.92z" />
            </svg>
          </div>
          <div style={{ textAlign: "left" }}>
            <p style={{ margin: 0, fontSize: 14, fontWeight: 800, color: "#473C33" }}>
              Need a real person?
            </p>
            <p style={{ margin: 0, fontSize: 12, fontWeight: 600, color: "#6b5a3a" }}>
              Tap to call for help
            </p>
          </div>
          <svg
            style={{ marginLeft: "auto" }}
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#473C33"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </button>
      </div>

      {/* Recent activity */}
      <div style={{ padding: "24px 24px 0" }}>
        <h3
          style={{
            margin: "0 0 12px",
            fontSize: 13,
            fontWeight: 800,
            color: "#8A7F6E",
            textTransform: "uppercase",
            letterSpacing: "0.08em",
          }}
        >
          Recent Activity
        </h3>
        <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <ActivityRow
            icon="🔍"
            label="ID record checked"
            date="12 Aug 2026"
            status="clear"
          />
          <ActivityRow
            icon="📄"
            label="Passport status checked"
            date="3 Aug 2026"
            status="in-progress"
          />
          <ActivityRow
            icon="💬"
            label="Asked about ID renewal"
            date="28 Jul 2026"
            status="done"
          />
        </div>
      </div>

      {/* Bottom padding for bird */}
      <div style={{ height: 100 }} />
    </div>
  )
}

function ActionCard({
  color,
  textColor,
  icon,
  title,
  subtitle,
  linkLabel,
  onPress,
}: {
  color: string
  textColor: string
  icon: React.ReactNode
  title: string
  subtitle: string
  linkLabel: string
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
        backgroundColor: color,
        border: "none",
        borderRadius: 22,
        padding: "22px 22px 20px",
        cursor: "pointer",
        transition: "all 0.15s ease",
        transform: pressed ? "scale(0.97)" : "scale(1)",
        boxShadow: pressed
          ? "none"
          : `0 6px 20px ${color}88`,
        display: "flex",
        alignItems: "flex-start",
        gap: 16,
        textAlign: "left",
      }}
    >
      <div
        style={{
          width: 52,
          height: 52,
          borderRadius: 16,
          backgroundColor: "rgba(255,255,255,0.25)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
        }}
      >
        {icon}
      </div>
      <div style={{ flex: 1 }}>
        <h3
          style={{
            margin: "0 0 4px",
            fontSize: 18,
            fontFamily: "'DM Serif Display', serif",
            color: textColor,
            lineHeight: 1.2,
          }}
        >
          {title}
        </h3>
        <p style={{ margin: "0 0 14px", fontSize: 13, color: textColor, opacity: 0.75, fontWeight: 600 }}>
          {subtitle}
        </p>
        <span
          style={{
            fontSize: 13,
            fontWeight: 800,
            color: textColor,
            display: "flex",
            alignItems: "center",
            gap: 4,
          }}
        >
          {linkLabel}
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={textColor} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </span>
      </div>
    </button>
  )
}

function ActivityRow({
  icon,
  label,
  date,
  status,
}: {
  icon: string
  label: string
  date: string
  status: "clear" | "in-progress" | "done"
}) {
  const statusColor =
    status === "clear" ? "#ABC270" : status === "in-progress" ? "#FEC868" : "#C8C2B4"
  const statusLabel =
    status === "clear" ? "Clear" : status === "in-progress" ? "In progress" : "Done"
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 12,
        padding: "12px 14px",
        backgroundColor: "#F5F1E4",
        borderRadius: 14,
        marginBottom: 6,
      }}
    >
      <span style={{ fontSize: 18 }}>{icon}</span>
      <div style={{ flex: 1 }}>
        <p style={{ margin: 0, fontSize: 13, fontWeight: 700, color: "#473C33" }}>{label}</p>
        <p style={{ margin: 0, fontSize: 11, color: "#8A7F6E", fontWeight: 600 }}>{date}</p>
      </div>
      <span
        style={{
          fontSize: 11,
          fontWeight: 800,
          color: status === "clear" ? "#2d3d18" : status === "in-progress" ? "#473C33" : "#8A7F6E",
          backgroundColor: statusColor,
          borderRadius: 8,
          padding: "3px 9px",
        }}
      >
        {statusLabel}
      </span>
    </div>
  )
}

function ShieldCardIcon() {
  return (
    <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
      <path
        d="M14 2.5L5 6v6c0 5.5 3.8 10.8 9 12.5 5.2-1.7 9-7 9-12.5V6L14 2.5z"
        fill="rgba(255,255,255,0.5)"
        stroke="rgba(255,255,255,0.8)"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      <path
        d="M9.5 14l3.5 3.5 6-6"
        stroke="white"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function ChatCardIcon() {
  return (
    <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
      <path
        d="M4 5h20a2 2 0 012 2v11a2 2 0 01-2 2H9l-5 4V7a2 2 0 012-2z"
        fill="rgba(255,255,255,0.4)"
        stroke="rgba(255,255,255,0.8)"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      <circle cx="10" cy="12" r="1.5" fill="white" />
      <circle cx="14" cy="12" r="1.5" fill="white" />
      <circle cx="18" cy="12" r="1.5" fill="white" />
    </svg>
  )
}
