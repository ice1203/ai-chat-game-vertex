'use client'

import { createContext, useContext, useReducer, type ReactNode } from 'react'
import type { ChatState, ChatContextValue, ConversationResponse } from '@/types'
import { sendConversationMessage } from '@/lib/api'

// Action types
export type ChatAction =
  | { type: 'SEND_MESSAGE_START'; userMessage: string }
  | { type: 'SEND_MESSAGE_SUCCESS'; response: ConversationResponse }
  | { type: 'SEND_MESSAGE_ERROR' }
  | { type: 'CLEAR_HISTORY' }

export const initialState: ChatState = {
  messages: [],
  currentImageUrl: '',
  isLoading: false,
  isGeneratingImage: false,
  affinityLevel: 0,
  sessionId: null,
}

export function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case 'SEND_MESSAGE_START':
      return {
        ...state,
        isLoading: true,
        isGeneratingImage: true,
        messages: [
          ...state.messages,
          {
            role: 'user',
            dialogue: action.userMessage,
            timestamp: new Date().toISOString(),
          },
        ],
      }

    case 'SEND_MESSAGE_SUCCESS':
      return {
        ...state,
        isLoading: false,
        isGeneratingImage: false,
        messages: [
          ...state.messages,
          {
            role: 'agent',
            dialogue: action.response.dialogue,
            narration: action.response.narration,
            timestamp: action.response.timestamp,
          },
        ],
        currentImageUrl: action.response.image_url ?? state.currentImageUrl,
        affinityLevel: action.response.affinity_level,
        sessionId: action.response.session_id,
      }

    case 'SEND_MESSAGE_ERROR':
      return {
        ...state,
        isLoading: false,
        isGeneratingImage: false,
      }

    case 'CLEAR_HISTORY':
      return { ...initialState }

    default:
      return state
  }
}

const ChatContext = createContext<ChatContextValue | null>(null)

export function ChatProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(chatReducer, initialState)

  async function sendMessage(message: string): Promise<void> {
    dispatch({ type: 'SEND_MESSAGE_START', userMessage: message })
    try {
      const response = await sendConversationMessage({
        user_id: 'demo-user',
        message,
        session_id: state.sessionId ?? undefined,
      })
      dispatch({ type: 'SEND_MESSAGE_SUCCESS', response })
    } catch {
      dispatch({ type: 'SEND_MESSAGE_ERROR' })
    }
  }

  function clearHistory(): void {
    dispatch({ type: 'CLEAR_HISTORY' })
  }

  return (
    <ChatContext.Provider value={{ state, sendMessage, clearHistory }}>
      {children}
    </ChatContext.Provider>
  )
}

export function useChat(): ChatContextValue {
  const context = useContext(ChatContext)
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider')
  }
  return context
}
