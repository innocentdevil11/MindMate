import './globals.css'
import { Inter } from 'next/font/google'
import AnimatedBackground from '@/components/AnimatedBackground.jsx'
const inter = Inter({ subsets: ['latin'] })

export const metadata = {
    title: 'MindMate',
    description: 'AI-powered multi-mind decision system',
}

export default function RootLayout({ children }) {
    return (
        <html lang="en">
            <body className={inter.className}>
                <AnimatedBackground />
                
                <main className="relative z-10">
                    {children}
                </main>
            </body>
        </html>
    )
}