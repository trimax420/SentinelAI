// src/components/Sidebar.tsx


import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Shield, Camera, Users, Map, Settings, LogOut, Bell } from 'lucide-react';

const Sidebar: React.FC = () => {
  const pathname = usePathname();

  return (
    <div className="bg-gray-900 text-white w-16 md:w-64 flex flex-col">
      {/* Logo and Title - Links to dashboard */}
      <Link href="/" className="flex items-center justify-center md:justify-start px-4 py-6">
        <Shield className="h-8 w-8 text-blue-400" />
        <span className="ml-2 text-xl font-bold hidden md:block">SecureWatch</span>
      </Link>
      
      {/* Navigation */}
      <nav className="flex-1 px-2 py-4">
        <div className="space-y-1">
          <Link 
            href="/cameras" 
            className={`flex items-center px-2 py-3 rounded hover:bg-gray-800 ${
              pathname === '/cameras' ? 'text-blue-400' : 'text-gray-300'
            }`}
          >
            <Camera className="h-5 w-5" />
            <span className="ml-3 hidden md:block">Cameras</span>
          </Link>
          <Link 
            href="/cameras/manage" 
            className={`flex items-center px-2 py-2 rounded hover:bg-gray-800 ml-4 ${
              pathname === '/cameras/manage' ? 'text-blue-400' : 'text-gray-300'
            }`}
          >
            <Settings className="h-5 w-5" />
            <span className="ml-3 hidden md:block">Manage Cameras</span>
          </Link>
        </div>
        
        <div className="mt-4">
          <Link href="/alerts" className="flex items-center px-2 py-3 text-gray-300 rounded hover:bg-gray-800 mb-1">
            <Bell className="h-5 w-5" />
            <span className="ml-3 hidden md:block">Alerts</span>
          </Link>
          
          <Link href="/personnel" className="flex items-center px-2 py-3 text-gray-300 rounded hover:bg-gray-800 mb-1">
            <Users className="h-5 w-5" />
            <span className="ml-3 hidden md:block">Personnel</span>
          </Link>
          
          <Link href="/map" className="flex items-center px-2 py-3 text-gray-300 rounded hover:bg-gray-800 mb-1">
            <Map className="h-5 w-5" />
            <span className="ml-3 hidden md:block">Store Map</span>
          </Link>
        </div>
      </nav>
      
      {/* Settings & Logout */}
      <div className="px-2 py-4 border-t border-gray-800">
        <Link href="/settings" className="flex items-center px-2 py-3 text-gray-300 rounded hover:bg-gray-800 mb-1">
          <Settings className="h-5 w-5" />
          <span className="ml-3 hidden md:block">Settings</span>
        </Link>
        
        <button className="w-full flex items-center px-2 py-3 text-gray-300 rounded hover:bg-gray-800">
          <LogOut className="h-5 w-5" />
          <span className="ml-3 hidden md:block">Logout</span>
        </button>
      </div>
    </div>
  );
};

export default Sidebar;