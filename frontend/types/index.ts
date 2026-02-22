/** Emotion states for character expressions */
export type Emotion = 'happy' | 'sad' | 'neutral' | 'surprised' | 'thoughtful'

/** Scene backgrounds */
export type Scene = 'indoor' | 'outdoor' | 'cafe' | 'park'

/** Message sender role */
export type Role = 'user' | 'agent'

/** Request payload for sending a message */
export interface ConversationRequest {
  user_id: string
  message: string
  session_id?: string
}

/** Response from the conversation endpoint */
export interface ConversationResponse {
  session_id: string
  dialogue: string
  narration: string
  emotion: Emotion
  scene: Scene
  image_url?: string
  affinity_level: number
  timestamp: string
}

/** A single message in the conversation log */
export interface Message {
  role: Role
  dialogue: string
  narration?: string
  timestamp: string
}

/** Chat state managed by ChatContext */
export interface ChatState {
  messages: Message[]
  currentImageUrl: string
  isLoading: boolean
  isGeneratingImage: boolean
  affinityLevel: number
  sessionId: string | null
}

/** Value provided by ChatContext */
export interface ChatContextValue {
  state: ChatState
  sendMessage: (message: string) => Promise<void>
  clearHistory: () => void
}
