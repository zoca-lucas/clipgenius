import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import Providers from '@/components/Providers'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'ClipGenius - Gerador de Cortes com IA',
  description: 'Transforme vídeos longos em cortes virais automaticamente usando IA',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="pt-BR">
      <body className={inter.className}>
        <Providers>
          <div className="min-h-screen bg-dark-900">
            {children}
          </div>
        </Providers>
      </body>
    </html>
  )
}
