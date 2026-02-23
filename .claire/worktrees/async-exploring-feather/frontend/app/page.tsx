import { ChatProvider } from '@/contexts/ChatContext'
import { ChatPage } from '@/components/ChatPage'

export default function Home() {
  return (
    <ChatProvider>
      <ChatPage />
    </ChatProvider>
  )
}
