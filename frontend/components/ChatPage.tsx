'use client'

import { useChat } from '@/contexts/ChatContext'
import { CharacterImageDisplay } from '@/components/CharacterImageDisplay'
import { ConversationLog } from '@/components/ConversationLog'
import { MessageInput } from '@/components/MessageInput'

export function ChatPage() {
  const { state, sendMessage } = useChat()

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-zinc-50 dark:bg-zinc-900 p-4">
      <div className="w-full max-w-xl flex flex-col gap-4">
        <CharacterImageDisplay
          imageUrl={state.currentImageUrl}
          isGenerating={state.isGeneratingImage}
        />
        <ConversationLog messages={state.messages} />
        <MessageInput onSend={sendMessage} isLoading={state.isLoading} />
      </div>
    </div>
  )
}
