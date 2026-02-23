import type {
  Emotion,
  Scene,
  Role,
  ConversationRequest,
  ConversationResponse,
  Message,
  ChatState,
  ChatContextValue,
  CharacterImageDisplayProps,
  ConversationLogProps,
  MessageInputProps,
} from '@/types'

describe('TypeScript type definitions', () => {
  describe('Emotion literal union type', () => {
    it('should accept all valid emotion values', () => {
      const emotions: Emotion[] = ['happy', 'sad', 'neutral', 'surprised', 'thoughtful']
      expect(emotions).toHaveLength(5)
      expect(emotions).toContain('happy')
      expect(emotions).toContain('sad')
      expect(emotions).toContain('neutral')
      expect(emotions).toContain('surprised')
      expect(emotions).toContain('thoughtful')
    })
  })

  describe('Scene literal union type', () => {
    it('should accept all valid scene values', () => {
      const scenes: Scene[] = ['indoor', 'outdoor', 'cafe', 'park']
      expect(scenes).toHaveLength(4)
      expect(scenes).toContain('indoor')
      expect(scenes).toContain('outdoor')
      expect(scenes).toContain('cafe')
      expect(scenes).toContain('park')
    })
  })

  describe('Role literal union type', () => {
    it('should accept user and agent roles', () => {
      const roles: Role[] = ['user', 'agent']
      expect(roles).toHaveLength(2)
    })
  })

  describe('ConversationRequest interface', () => {
    it('should create a valid request with required fields', () => {
      const request: ConversationRequest = {
        user_id: 'test-user',
        message: 'Hello',
      }
      expect(request.user_id).toBe('test-user')
      expect(request.message).toBe('Hello')
      expect(request.session_id).toBeUndefined()
    })

    it('should create a valid request with optional session_id', () => {
      const request: ConversationRequest = {
        user_id: 'test-user',
        message: 'Hello',
        session_id: 'session-123',
      }
      expect(request.session_id).toBe('session-123')
    })
  })

  describe('ConversationResponse interface', () => {
    it('should create a valid response with all required fields', () => {
      const response: ConversationResponse = {
        session_id: 'session-123',
        dialogue: 'Hi there!',
        narration: 'She smiled warmly.',
        emotion: 'happy',
        scene: 'cafe',
        affinity_level: 50,
        timestamp: '2026-02-23T10:00:00Z',
      }
      expect(response.session_id).toBe('session-123')
      expect(response.dialogue).toBe('Hi there!')
      expect(response.emotion).toBe('happy')
      expect(response.scene).toBe('cafe')
      expect(response.affinity_level).toBe(50)
      expect(response.image_url).toBeUndefined()
    })

    it('should allow optional image_url', () => {
      const response: ConversationResponse = {
        session_id: 'session-123',
        dialogue: 'Hi there!',
        narration: 'She smiled warmly.',
        emotion: 'happy',
        scene: 'cafe',
        image_url: '/data/images/happy_cafe_20260223.png',
        affinity_level: 50,
        timestamp: '2026-02-23T10:00:00Z',
      }
      expect(response.image_url).toBe('/data/images/happy_cafe_20260223.png')
    })
  })

  describe('Message interface', () => {
    it('should create a valid user message', () => {
      const message: Message = {
        role: 'user',
        dialogue: 'Hello',
        timestamp: '2026-02-23T10:00:00Z',
      }
      expect(message.role).toBe('user')
      expect(message.narration).toBeUndefined()
    })

    it('should create a valid agent message with narration', () => {
      const message: Message = {
        role: 'agent',
        dialogue: 'Hi there!',
        narration: 'She smiled warmly.',
        timestamp: '2026-02-23T10:00:00Z',
      }
      expect(message.narration).toBe('She smiled warmly.')
    })
  })

  describe('ChatState interface', () => {
    it('should create a valid initial chat state', () => {
      const state: ChatState = {
        messages: [],
        currentImageUrl: '',
        isLoading: false,
        isGeneratingImage: false,
        affinityLevel: 0,
        sessionId: null,
      }
      expect(state.messages).toHaveLength(0)
      expect(state.isLoading).toBe(false)
      expect(state.sessionId).toBeNull()
    })

    it('should accept sessionId as a string', () => {
      const state: ChatState = {
        messages: [],
        currentImageUrl: '/images/char.png',
        isLoading: true,
        isGeneratingImage: true,
        affinityLevel: 75,
        sessionId: 'active-session',
      }
      expect(state.sessionId).toBe('active-session')
      expect(state.affinityLevel).toBe(75)
    })
  })

  describe('ChatContextValue interface', () => {
    it('should create a valid chat context value', () => {
      const mockSendMessage = jest.fn().mockResolvedValue(undefined)
      const mockClearHistory = jest.fn()
      const contextValue: ChatContextValue = {
        state: {
          messages: [],
          currentImageUrl: '',
          isLoading: false,
          isGeneratingImage: false,
          affinityLevel: 0,
          sessionId: null,
        },
        sendMessage: mockSendMessage,
        clearHistory: mockClearHistory,
      }
      expect(typeof contextValue.sendMessage).toBe('function')
      expect(typeof contextValue.clearHistory).toBe('function')
    })
  })

  describe('CharacterImageDisplayProps interface', () => {
    it('should create valid props with imageUrl and isGenerating=false', () => {
      const props: CharacterImageDisplayProps = {
        imageUrl: '/images/character.png',
        isGenerating: false,
      }
      expect(props.imageUrl).toBe('/images/character.png')
      expect(props.isGenerating).toBe(false)
    })

    it('should accept isGenerating as true', () => {
      const props: CharacterImageDisplayProps = {
        imageUrl: '',
        isGenerating: true,
      }
      expect(props.isGenerating).toBe(true)
    })
  })

  describe('ConversationLogProps interface', () => {
    it('should create valid props with empty messages array', () => {
      const props: ConversationLogProps = { messages: [] }
      expect(props.messages).toHaveLength(0)
    })

    it('should create valid props with multiple messages', () => {
      const props: ConversationLogProps = {
        messages: [
          { role: 'user', dialogue: 'Hello', timestamp: '2026-02-23T10:00:00Z' },
          { role: 'agent', dialogue: 'Hi!', narration: 'She smiled.', timestamp: '2026-02-23T10:00:01Z' },
        ],
      }
      expect(props.messages).toHaveLength(2)
      expect(props.messages[0].role).toBe('user')
      expect(props.messages[1].role).toBe('agent')
    })
  })

  describe('MessageInputProps interface', () => {
    it('should create valid props with onSend callback and isLoading=false', () => {
      const mockOnSend = jest.fn()
      const props: MessageInputProps = {
        onSend: mockOnSend,
        isLoading: false,
      }
      expect(props.isLoading).toBe(false)
      expect(typeof props.onSend).toBe('function')
    })

    it('should accept isLoading as true', () => {
      const mockOnSend = jest.fn()
      const props: MessageInputProps = {
        onSend: mockOnSend,
        isLoading: true,
      }
      expect(props.isLoading).toBe(true)
    })

    it('should accept onSend as a function that takes a string', () => {
      let receivedMessage = ''
      const props: MessageInputProps = {
        onSend: (message: string) => { receivedMessage = message },
        isLoading: false,
      }
      props.onSend('Test message')
      expect(receivedMessage).toBe('Test message')
    })
  })
})
