const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"

export type FlagSeverity = "low" | "medium" | "high"

export type Flag = {
  type: string
  severity: FlagSeverity
  title: string
  plainExplanation: string
  nextSteps: string[]
}

export type CheckIdentityResponse = {
  found: boolean
  idNumber: string
  flags: Flag[]
  cleanRecord: boolean
  message?: string
}

export type Location = { lat: number; lng: number }

export type NearestBranch = {
  name: string
  address: string
  distanceKm: number
}

export type ChatResponse = {
  reply: string
  documentsNeeded: string[]
  estimatedCost: string
  estimatedTime: string
  nearestBranch: NearestBranch | null
  conversationId?: string
}

type ApiErrorBody = {
  error: true
  message: string
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })

  const data = await res.json()

  if (!res.ok || (data as ApiErrorBody).error) {
    throw new Error((data as ApiErrorBody).message || "Something went wrong. Please try again.")
  }

  return data as T
}

export function checkIdentity(idNumber: string): Promise<CheckIdentityResponse> {
  return postJson<CheckIdentityResponse>("/api/check-identity", { idNumber })
}

export function sendChatMessage(
  message: string,
  conversationId: string,
  location?: Location,
): Promise<ChatResponse> {
  return postJson<ChatResponse>("/api/chat", { message, conversationId, location })
}
