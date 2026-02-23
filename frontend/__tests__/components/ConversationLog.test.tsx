import { render, screen } from '@testing-library/react'
import { ConversationLog } from '@/components/ConversationLog'
import type { Message } from '@/types'

// scrollIntoView is not implemented in jsdom
beforeAll(() => {
  window.HTMLElement.prototype.scrollIntoView = jest.fn()
})

const userMessage: Message = {
  role: 'user',
  dialogue: 'Hello there!',
  timestamp: '2026-02-23T10:00:00Z',
}

const agentMessage: Message = {
  role: 'agent',
  dialogue: 'Nice to meet you!',
  narration: 'She smiled warmly.',
  timestamp: '2026-02-23T10:01:00Z',
}

describe('ConversationLog', () => {
  describe('empty state', () => {
    it('should render without errors when messages is empty', () => {
      const { container } = render(<ConversationLog messages={[]} />)
      expect(container).toBeInTheDocument()
    })
  })

  describe('message rendering', () => {
    it('should render user message dialogue', () => {
      render(<ConversationLog messages={[userMessage]} />)
      expect(screen.getByText('Hello there!')).toBeInTheDocument()
    })

    it('should render agent message dialogue', () => {
      render(<ConversationLog messages={[agentMessage]} />)
      expect(screen.getByText('Nice to meet you!')).toBeInTheDocument()
    })

    it('should render agent message narration', () => {
      render(<ConversationLog messages={[agentMessage]} />)
      expect(screen.getByText('She smiled warmly.')).toBeInTheDocument()
    })

    it('should not show narration field when absent', () => {
      render(<ConversationLog messages={[userMessage]} />)
      // User message has no narration
      const narrations = document.querySelectorAll('[data-testid="narration"]')
      expect(narrations).toHaveLength(0)
    })

    it('should render multiple messages', () => {
      render(<ConversationLog messages={[userMessage, agentMessage]} />)
      expect(screen.getByText('Hello there!')).toBeInTheDocument()
      expect(screen.getByText('Nice to meet you!')).toBeInTheDocument()
    })
  })

  describe('message alignment', () => {
    it('should apply user alignment class to user messages', () => {
      render(<ConversationLog messages={[userMessage]} />)
      const messageWrapper = screen.getByText('Hello there!').closest('[data-role]')
      expect(messageWrapper).toHaveAttribute('data-role', 'user')
    })

    it('should apply agent alignment class to agent messages', () => {
      render(<ConversationLog messages={[agentMessage]} />)
      const messageWrapper = screen.getByText('Nice to meet you!').closest('[data-role]')
      expect(messageWrapper).toHaveAttribute('data-role', 'agent')
    })
  })

  describe('auto-scroll', () => {
    it('should call scrollIntoView when messages change', () => {
      const { rerender } = render(<ConversationLog messages={[]} />)
      const scrollIntoViewMock = window.HTMLElement.prototype.scrollIntoView as jest.Mock
      scrollIntoViewMock.mockClear()

      rerender(<ConversationLog messages={[userMessage]} />)
      expect(scrollIntoViewMock).toHaveBeenCalled()
    })
  })

  describe('scroll area', () => {
    it('should wrap content in scroll area', () => {
      render(<ConversationLog messages={[]} />)
      expect(document.querySelector('[data-slot="scroll-area"]')).toBeInTheDocument()
    })
  })
})
