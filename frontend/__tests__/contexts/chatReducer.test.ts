import { chatReducer, initialState } from '@/contexts/ChatContext'
import type { ChatAction } from '@/contexts/ChatContext'
import type { ConversationResponse } from '@/types'

describe('chatReducer', () => {
  describe('SEND_MESSAGE_START', () => {
    it('should set isLoading to true', () => {
      const action: ChatAction = { type: 'SEND_MESSAGE_START', userMessage: 'Hello' }
      const next = chatReducer(initialState, action)
      expect(next.isLoading).toBe(true)
    })

    it('should set isGeneratingImage to true', () => {
      const action: ChatAction = { type: 'SEND_MESSAGE_START', userMessage: 'Hello' }
      const next = chatReducer(initialState, action)
      expect(next.isGeneratingImage).toBe(true)
    })

    it('should add user message to messages', () => {
      const action: ChatAction = { type: 'SEND_MESSAGE_START', userMessage: 'Hello there' }
      const next = chatReducer(initialState, action)
      expect(next.messages).toHaveLength(1)
      expect(next.messages[0].role).toBe('user')
      expect(next.messages[0].dialogue).toBe('Hello there')
    })

    it('should not modify other state fields', () => {
      const action: ChatAction = { type: 'SEND_MESSAGE_START', userMessage: 'Hi' }
      const next = chatReducer(initialState, action)
      expect(next.currentImageUrl).toBe(initialState.currentImageUrl)
      expect(next.affinityLevel).toBe(initialState.affinityLevel)
      expect(next.sessionId).toBe(initialState.sessionId)
    })
  })

  describe('SEND_MESSAGE_SUCCESS', () => {
    const stateWithUserMsg = chatReducer(initialState, {
      type: 'SEND_MESSAGE_START',
      userMessage: 'Hello',
    })

    const mockResponse: ConversationResponse = {
      session_id: 'session-abc',
      dialogue: 'Hi there!',
      narration: 'She smiled warmly.',
      emotion: 'happy',
      scene: 'cafe',
      image_url: '/images/happy_cafe.png',
      affinity_level: 15,
      timestamp: '2026-02-23T10:00:00Z',
    }

    it('should set isLoading to false', () => {
      const action: ChatAction = { type: 'SEND_MESSAGE_SUCCESS', response: mockResponse }
      const next = chatReducer(stateWithUserMsg, action)
      expect(next.isLoading).toBe(false)
    })

    it('should set isGeneratingImage to false', () => {
      const action: ChatAction = { type: 'SEND_MESSAGE_SUCCESS', response: mockResponse }
      const next = chatReducer(stateWithUserMsg, action)
      expect(next.isGeneratingImage).toBe(false)
    })

    it('should add agent message to messages', () => {
      const action: ChatAction = { type: 'SEND_MESSAGE_SUCCESS', response: mockResponse }
      const next = chatReducer(stateWithUserMsg, action)
      expect(next.messages).toHaveLength(2) // user + agent
      const agentMsg = next.messages[1]
      expect(agentMsg.role).toBe('agent')
      expect(agentMsg.dialogue).toBe('Hi there!')
      expect(agentMsg.narration).toBe('She smiled warmly.')
      expect(agentMsg.timestamp).toBe('2026-02-23T10:00:00Z')
    })

    it('should update currentImageUrl when image_url is provided', () => {
      const action: ChatAction = { type: 'SEND_MESSAGE_SUCCESS', response: mockResponse }
      const next = chatReducer(stateWithUserMsg, action)
      expect(next.currentImageUrl).toBe('/images/happy_cafe.png')
    })

    it('should preserve currentImageUrl when image_url is undefined', () => {
      const stateWithImage = { ...stateWithUserMsg, currentImageUrl: '/images/prev.png' }
      const responseNoImage: ConversationResponse = { ...mockResponse, image_url: undefined }
      const action: ChatAction = { type: 'SEND_MESSAGE_SUCCESS', response: responseNoImage }
      const next = chatReducer(stateWithImage, action)
      expect(next.currentImageUrl).toBe('/images/prev.png')
    })

    it('should update affinityLevel from response', () => {
      const action: ChatAction = { type: 'SEND_MESSAGE_SUCCESS', response: mockResponse }
      const next = chatReducer(stateWithUserMsg, action)
      expect(next.affinityLevel).toBe(15)
    })

    it('should update sessionId from response', () => {
      const action: ChatAction = { type: 'SEND_MESSAGE_SUCCESS', response: mockResponse }
      const next = chatReducer(stateWithUserMsg, action)
      expect(next.sessionId).toBe('session-abc')
    })
  })

  describe('SEND_MESSAGE_ERROR', () => {
    const stateWithUserMsg = chatReducer(initialState, {
      type: 'SEND_MESSAGE_START',
      userMessage: 'Hello',
    })

    it('should set isLoading to false', () => {
      const action: ChatAction = { type: 'SEND_MESSAGE_ERROR' }
      const next = chatReducer(stateWithUserMsg, action)
      expect(next.isLoading).toBe(false)
    })

    it('should set isGeneratingImage to false', () => {
      const action: ChatAction = { type: 'SEND_MESSAGE_ERROR' }
      const next = chatReducer(stateWithUserMsg, action)
      expect(next.isGeneratingImage).toBe(false)
    })

    it('should keep the user message in messages', () => {
      const action: ChatAction = { type: 'SEND_MESSAGE_ERROR' }
      const next = chatReducer(stateWithUserMsg, action)
      expect(next.messages).toHaveLength(1)
      expect(next.messages[0].role).toBe('user')
    })

    it('should not change affinityLevel or sessionId', () => {
      const action: ChatAction = { type: 'SEND_MESSAGE_ERROR' }
      const next = chatReducer(stateWithUserMsg, action)
      expect(next.affinityLevel).toBe(initialState.affinityLevel)
      expect(next.sessionId).toBe(initialState.sessionId)
    })
  })

  describe('CLEAR_HISTORY', () => {
    it('should reset to initial state', () => {
      const stateWithData: typeof initialState = {
        messages: [{ role: 'user', dialogue: 'Hi', timestamp: '2026-02-23T10:00:00Z' }],
        currentImageUrl: '/images/test.png',
        isLoading: false,
        isGeneratingImage: false,
        affinityLevel: 50,
        sessionId: 'session-xyz',
      }
      const action: ChatAction = { type: 'CLEAR_HISTORY' }
      const next = chatReducer(stateWithData, action)
      expect(next).toEqual(initialState)
    })
  })
})
