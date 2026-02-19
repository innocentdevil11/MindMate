import './globals.css'
import { Inter } from 'next/font/google'
import AnimatedBackground from '@/components/AnimatedBackground.jsx'
// NEW: Auth provider wraps the entire app for auth state access
import { AuthProvider } from '@/context/AuthContext'

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
                {/* WHY AuthProvider here: Every page and component needs access
                    to auth state (user, session, signOut). Wrapping at layout level
                    ensures it's available everywhere without prop drilling. */}
                <AuthProvider>
                    <main className="relative z-10">
                        {children}
                    </main>
                </AuthProvider>
            </body>
        </html>
    )
}