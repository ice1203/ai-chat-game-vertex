import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ChatProvider, useChat } from '@/contexts/ChatContext'
import * as api from '@/lib/api'

jest.mock('@/lib/api')

const mockSendConversationMessage = api.sendConversationMessage as jest.MockedFunction<
  typeof api.sendConversationMessage
>

function TestComponent() {
  const { state, sendMessage, clearHistory } = useChat()
  return (
    <div>
      <div data-testid="loading">{state.isLoading.toString()}</div>
      <div data-testid="generating">{state.isGeneratingImage.toString()}</div>
      <div data-testid="message-count">{state.messages.length}</div>
      <div data-testid="affinity">{state.affinityLevel}</div>
      <div data-testid="session-id">{state.sessionId ?? 'null'}</div>
      <div data-testid="image-url">{state.currentImageUrl}</div>
      <button onClick={() => sendMessage('Hello')}>Send</button>
      <button onClick={clearHistory}>Clear</button>
    </div>
  )
}

describe('ChatContext', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('initial state', () => {
    it('should provide correct initial state', () => {
      render(
        <ChatProvider>
          <TestComponent />
        </ChatProvider>
      )
      expect(screen.getByTestId('loading').textContent).toBe('false')
      expect(screen.getByTestId('generating').textContent).toBe('false')
      expect(screen.getByTestId('message-count').textContent).toBe('0')
      expect(screen.getByTestId('affinity').textContent).toBe('0')
      expect(screen.getByTestId('session-id').textContent).toBe('null')
      expect(screen.getByTestId('image-url').textContent).toBe('')
    })
  })

  describe('sendMessage', () => {
    it('should set loading state and add user message immediately', async () => {
      mockSendConversationMessage.mockImplementation(
        () => new Promise(() => {}) // never resolves
      )

      render(
        <ChatProvider>
          <TestComponent />
        </ChatProvider>
      )

      fireEvent.click(screen.getByText('Send'))

      expect(screen.getByTestId('loading').textContent).toBe('true')
      expect(screen.getByTestId('generating').textContent).toBe('true')
      expect(screen.getByTestId('message-count').textContent).toBe('1')
    })

    it('should update state on successful API response', async () => {
      const mockResponse = {
        session_id: 'session-123',
        dialogue: 'Nice to meet you!',
        narration: 'She smiled.',
        emotion: 'happy' as const,
        scene: 'cafe' as const,
        image_url: '/images/happy_cafe_001.png',
        affinity_level: 10,
        timestamp: '2026-02-23T10:00:00Z',
      }
      mockSendConversationMessage.mockResolvedValue(mockResponse)

      render(
        <ChatProvider>
          <TestComponent />
        </ChatProvider>
      )

      fireEvent.click(screen.getByText('Send'))

      await waitFor(() => {
        expect(screen.getByTestId('loading').textContent).toBe('false')
      })

      expect(screen.getByTestId('generating').textContent).toBe('false')
      expect(screen.getByTestId('message-count').textContent).toBe('2')
      expect(screen.getByTestId('affinity').textContent).toBe('10')
      expect(screen.getByTestId('session-id').textContent).toBe('session-123')
      expect(screen.getByTestId('image-url').textContent).toBe('/images/happy_cafe_001.png')
    })

    it('should pass session_id from state in subsequent calls', async () => {
      const mockResponse = {
        session_id: 'session-xyz',
        dialogue: 'Hi!',
        narration: '',
        emotion: 'neutral' as const,
        scene: 'indoor' as const,
        affinity_level: 5,
        timestamp: '2026-02-23T10:00:00Z',
      }
      mockSendConversationMessage.mockResolvedValue(mockResponse)

      render(
        <ChatProvider>
          <TestComponent />
        </ChatProvider>
      )

      fireEvent.click(screen.getByText('Send'))
      await waitFor(() => expect(screen.getByTestId('session-id').textContent).toBe('session-xyz'))

      // Second call should use the session_id from state
      fireEvent.click(screen.getByText('Send'))
      await waitFor(() => expect(mockSendConversationMessage).toHaveBeenCalledTimes(2))

      const secondCall = mockSendConversationMessage.mock.calls[1][0]
      expect(secondCall.session_id).toBe('session-xyz')
    })

    it('should reset loading state on API error', async () => {
      mockSendConversationMessage.mockRejectedValue(new Error('Network Error'))

      render(
        <ChatProvider>
          <TestComponent />
        </ChatProvider>
      )

      fireEvent.click(screen.getByText('Send'))

      await waitFor(() => {
        expect(screen.getByTestId('loading').textContent).toBe('false')
      })

      expect(screen.getByTestId('generating').textContent).toBe('false')
      // User message is kept, no agent message added
      expect(screen.getByTestId('message-count').textContent).toBe('1')
      // Affinity and session unchanged
      expect(screen.getByTestId('affinity').textContent).toBe('0')
      expect(screen.getByTestId('session-id').textContent).toBe('null')
    })

    it('should call API with correct user_id and message', async () => {
      mockSendConversationMessage.mockResolvedValue({
        session_id: 's1',
        dialogue: 'Hi',
        narration: '',
        emotion: 'neutral' as const,
        scene: 'indoor' as const,
        affinity_level: 0,
        timestamp: '2026-02-23T10:00:00Z',
      })

      render(
        <ChatProvider>
          <TestComponent />
        </ChatProvider>
      )

      fireEvent.click(screen.getByText('Send'))
      await waitFor(() => expect(mockSendConversationMessage).toHaveBeenCalledTimes(1))

      expect(mockSendConversationMessage).toHaveBeenCalledWith(
        expect.objectContaining({
          user_id: 'demo-user',
          message: 'Hello',
        })
      )
    })
  })

  describe('clearHistory', () => {
    it('should reset all state to initial values', async () => {
      const mockResponse = {
        session_id: 'session-to-clear',
        dialogue: 'Hi!',
        narration: '',
        emotion: 'neutral' as const,
        scene: 'indoor' as const,
        image_url: '/images/test.png',
        affinity_level: 30,
        timestamp: '2026-02-23T10:00:00Z',
      }
      mockSendConversationMessage.mockResolvedValue(mockResponse)

      render(
        <ChatProvider>
          <TestComponent />
        </ChatProvider>
      )

      fireEvent.click(screen.getByText('Send'))
      await waitFor(() => {
        expect(screen.getByTestId('message-count').textContent).toBe('2')
      })

      fireEvent.click(screen.getByText('Clear'))

      expect(screen.getByTestId('message-count').textContent).toBe('0')
      expect(screen.getByTestId('affinity').textContent).toBe('0')
      expect(screen.getByTestId('session-id').textContent).toBe('null')
      expect(screen.getByTestId('image-url').textContent).toBe('')
    })
  })

  describe('useChat outside provider', () => {
    it('should throw error when used outside ChatProvider', () => {
      // Suppress console.error for this test
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {})

      expect(() => {
        render(<TestComponent />)
      }).toThrow('useChat must be used within a ChatProvider')

      consoleSpy.mockRestore()
    })
  })
})
