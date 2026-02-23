'use client'

import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import type { CharacterImageDisplayProps } from '@/types'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

function resolveImageUrl(imagePath: string): string {
  if (imagePath.startsWith('http')) return imagePath
  return `${API_BASE_URL}${imagePath}`
}

export function CharacterImageDisplay({ imageUrl, isGenerating }: CharacterImageDisplayProps) {
  return (
    <Card className="w-full">
      <CardContent className="flex items-center justify-center p-4">
        {isGenerating && !imageUrl ? (
          <Skeleton className="w-full aspect-square" />
        ) : imageUrl ? (
          <div className="relative w-full aspect-square">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={resolveImageUrl(imageUrl)}
              alt="Character"
              className="w-full h-full object-cover rounded-md transition-opacity duration-300"
            />
          </div>
        ) : (
          <div className="w-full aspect-square bg-muted flex items-center justify-center rounded-md">
            <span className="text-muted-foreground">キャラクター画像</span>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
