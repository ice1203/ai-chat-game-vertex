'use client'

import { useEffect, useRef } from 'react'
import { ScrollArea } from '@/components/ui/scroll-area'
import type { ConversationLogProps } from '@/types'

export function ConversationLog({ messages }: ConversationLogProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <ScrollArea className="h-64 w-full">
      <div className="flex flex-col gap-4 p-4">
        {messages.map((message, index) => (
          <div
            key={index}
            data-role={message.role}
            className={`flex flex-col ${message.role === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-4 py-2 ${
                message.role === 'user'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted'
              }`}
            >
              <p className="text-sm">{message.dialogue}</p>
              {message.narration && (
                <p className="text-xs text-muted-foreground mt-1 italic">
                  {message.narration}
                </p>
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  )
}
