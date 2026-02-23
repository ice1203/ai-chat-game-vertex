import type { ConversationRequest, ConversationResponse } from '@/types'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

export async function sendConversationMessage(
  request: ConversationRequest
): Promise<ConversationResponse> {
  const response = await fetch(`${API_BASE_URL}/api/conversation/send`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`)
  }
  return response.json() as Promise<ConversationResponse>
}
