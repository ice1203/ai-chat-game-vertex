import { render, screen } from '@testing-library/react'
import { CharacterImageDisplay } from '@/components/CharacterImageDisplay'

describe('CharacterImageDisplay', () => {
  describe('when isGenerating is true', () => {
    it('should show skeleton loader', () => {
      render(<CharacterImageDisplay imageUrl="" isGenerating={true} />)
      // Skeleton is rendered as a div with data-slot="skeleton"
      expect(document.querySelector('[data-slot="skeleton"]')).toBeInTheDocument()
    })

    it('should not show image when generating', () => {
      render(
        <CharacterImageDisplay imageUrl="/images/test.png" isGenerating={true} />
      )
      expect(screen.queryByRole('img')).not.toBeInTheDocument()
    })
  })

  describe('when isGenerating is false and imageUrl is provided', () => {
    it('should show image with correct src', () => {
      render(
        <CharacterImageDisplay imageUrl="/images/happy_cafe.png" isGenerating={false} />
      )
      const img = screen.getByRole('img')
      expect(img).toBeInTheDocument()
      expect(img).toHaveAttribute('src', '/images/happy_cafe.png')
    })

    it('should show image with alt text', () => {
      render(
        <CharacterImageDisplay imageUrl="/images/happy_cafe.png" isGenerating={false} />
      )
      expect(screen.getByAltText('Character')).toBeInTheDocument()
    })

    it('should not show skeleton', () => {
      render(
        <CharacterImageDisplay imageUrl="/images/happy_cafe.png" isGenerating={false} />
      )
      expect(document.querySelector('[data-slot="skeleton"]')).not.toBeInTheDocument()
    })
  })

  describe('when isGenerating is false and imageUrl is empty', () => {
    it('should show placeholder text', () => {
      render(<CharacterImageDisplay imageUrl="" isGenerating={false} />)
      expect(screen.getByText('キャラクター画像')).toBeInTheDocument()
    })

    it('should not show image', () => {
      render(<CharacterImageDisplay imageUrl="" isGenerating={false} />)
      expect(screen.queryByRole('img')).not.toBeInTheDocument()
    })
  })

  describe('Card wrapper', () => {
    it('should render inside a card container', () => {
      render(<CharacterImageDisplay imageUrl="" isGenerating={false} />)
      expect(document.querySelector('[data-slot="card"]')).toBeInTheDocument()
    })
  })
})
