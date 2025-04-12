import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import Link from 'next/link'
import { LayoutDashboard, Bell, Camera, Users, Map, Settings, Search, Shield } from 'lucide-react'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Security Hub',
  description: 'Security surveillance and monitoring system',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="flex h-screen">
          {/* Sidebar */}
          <div className="w-64 bg-gray-900 text-white p-6">
            <h1 className="text-xl font-bold mb-8">Security Hub</h1>
            <nav className="space-y-2">
              <Link href="/" className="flex items-center space-x-3 p-3 rounded-lg hover:bg-gray-800">
                <LayoutDashboard size={20} />
                <span>Dashboard</span>
              </Link>
              <Link href="/alerts" className="flex items-center space-x-3 p-3 rounded-lg hover:bg-gray-800">
                <Bell size={20} />
                <span>Alerts</span>
              </Link>
              <Link href="/cameras" className="flex items-center space-x-3 p-3 rounded-lg hover:bg-gray-800">
                <Camera size={20} />
                <span>Cameras</span>
              </Link>
              <Link href="/suspects" className="flex items-center space-x-3 p-3 rounded-lg hover:bg-gray-800">
                <Shield size={20} />
                <span>Suspects</span>
              </Link>
              <Link href="/store-map" className="flex items-center space-x-3 p-3 rounded-lg hover:bg-gray-800">
                <Map size={20} />
                <span>Store Map</span>
              </Link>
              <Link href="/settings" className="flex items-center space-x-3 p-3 rounded-lg hover:bg-gray-800">
                <Settings size={20} />
                <span>Settings</span>
              </Link>
            </nav>
          </div>

          {/* Main content */}
          <div className="flex-1 overflow-auto">
            {/* Top bar */}
            <div className="h-16 border-b flex items-center justify-between px-6">
              <div className="flex items-center space-x-3">
                <Search size={20} className="text-gray-400" />
                <input
                  type="text"
                  placeholder="Search..."
                  className="bg-gray-100 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex items-center space-x-4">
                <Bell size={20} className="text-gray-600" />
                <div className="w-8 h-8 bg-gray-200 rounded-full"></div>
              </div>
            </div>

            {/* Page content */}
            <main className="p-6">
              {children}
            </main>
          </div>
        </div>
      </body>
    </html>
  )
}
