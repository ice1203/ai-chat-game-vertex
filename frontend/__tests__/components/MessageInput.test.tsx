import { render, screen, fireEvent } from '@testing-library/react'
import { MessageInput } from '@/components/MessageInput'

describe('MessageInput', () => {
  describe('rendering', () => {
    it('should render an input field', () => {
      render(<MessageInput onSend={jest.fn()} isLoading={false} />)
      expect(screen.getByRole('textbox')).toBeInTheDocument()
    })

    it('should render a send button', () => {
      render(<MessageInput onSend={jest.fn()} isLoading={false} />)
      expect(screen.getByRole('button', { name: '送信' })).toBeInTheDocument()
    })
  })

  describe('sending messages', () => {
    it('should call onSend with message when button clicked', () => {
      const onSend = jest.fn()
      render(<MessageInput onSend={onSend} isLoading={false} />)

      const input = screen.getByRole('textbox')
      fireEvent.change(input, { target: { value: 'Hello!' } })
      fireEvent.click(screen.getByRole('button', { name: '送信' }))

      expect(onSend).toHaveBeenCalledWith('Hello!')
    })

    it('should call onSend when Enter key is pressed', () => {
      const onSend = jest.fn()
      render(<MessageInput onSend={onSend} isLoading={false} />)

      const input = screen.getByRole('textbox')
      fireEvent.change(input, { target: { value: 'Enter message' } })
      fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' })

      expect(onSend).toHaveBeenCalledWith('Enter message')
    })

    it('should clear input after sending', () => {
      render(<MessageInput onSend={jest.fn()} isLoading={false} />)

      const input = screen.getByRole('textbox')
      fireEvent.change(input, { target: { value: 'Hello!' } })
      fireEvent.click(screen.getByRole('button', { name: '送信' }))

      expect(input).toHaveValue('')
    })

    it('should trim whitespace before sending', () => {
      const onSend = jest.fn()
      render(<MessageInput onSend={onSend} isLoading={false} />)

      const input = screen.getByRole('textbox')
      fireEvent.change(input, { target: { value: '  Hello!  ' } })
      fireEvent.click(screen.getByRole('button', { name: '送信' }))

      expect(onSend).toHaveBeenCalledWith('Hello!')
    })
  })

  describe('empty message validation', () => {
    it('should not call onSend when message is empty', () => {
      const onSend = jest.fn()
      render(<MessageInput onSend={onSend} isLoading={false} />)

      fireEvent.click(screen.getByRole('button', { name: '送信' }))

      expect(onSend).not.toHaveBeenCalled()
    })

    it('should not call onSend when message is only whitespace', () => {
      const onSend = jest.fn()
      render(<MessageInput onSend={onSend} isLoading={false} />)

      const input = screen.getByRole('textbox')
      fireEvent.change(input, { target: { value: '   ' } })
      fireEvent.click(screen.getByRole('button', { name: '送信' }))

      expect(onSend).not.toHaveBeenCalled()
    })

    it('should not call onSend on Enter when message is empty', () => {
      const onSend = jest.fn()
      render(<MessageInput onSend={onSend} isLoading={false} />)

      const input = screen.getByRole('textbox')
      fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' })

      expect(onSend).not.toHaveBeenCalled()
    })

    it('should disable send button when message is empty', () => {
      render(<MessageInput onSend={jest.fn()} isLoading={false} />)
      expect(screen.getByRole('button', { name: '送信' })).toBeDisabled()
    })
  })

  describe('loading state', () => {
    it('should disable input when isLoading is true', () => {
      render(<MessageInput onSend={jest.fn()} isLoading={true} />)
      expect(screen.getByRole('textbox')).toBeDisabled()
    })

    it('should disable send button when isLoading is true', () => {
      render(<MessageInput onSend={jest.fn()} isLoading={true} />)
      expect(screen.getByRole('button', { name: '送信' })).toBeDisabled()
    })

    it('should not call onSend when isLoading is true and Enter is pressed', () => {
      const onSend = jest.fn()
      render(<MessageInput onSend={onSend} isLoading={true} />)

      const input = screen.getByRole('textbox')
      fireEvent.change(input, { target: { value: 'Hello' } })
      fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' })

      expect(onSend).not.toHaveBeenCalled()
    })
  })
})
