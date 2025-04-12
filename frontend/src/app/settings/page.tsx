"use client";

import { useState } from 'react';
import { Bell, Camera, Shield, Users } from 'lucide-react';

interface SettingSection {
  id: string;
  title: string;
  icon: React.ElementType;
  description: string;
}

const settingSections: SettingSection[] = [
  {
    id: 'notifications',
    title: 'Notifications',
    icon: Bell,
    description: 'Configure alert notifications and preferences',
  },
  {
    id: 'cameras',
    title: 'Camera Settings',
    icon: Camera,
    description: 'Manage camera configurations and detection settings',
  },
  {
    id: 'security',
    title: 'Security Rules',
    icon: Shield,
    description: 'Set up security rules and alert thresholds',
  },
  {
    id: 'users',
    title: 'User Management',
    icon: Users,
    description: 'Manage user accounts and permissions',
  },
];

export default function SettingsPage() {
  const [activeSection, setActiveSection] = useState<string>('notifications');

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold text-gray-900">Settings</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-1">
          <nav className="space-y-1">
            {settingSections.map((section) => (
              <button
                key={section.id}
                className={`w-full flex items-center px-4 py-2 text-sm font-medium rounded-md ${
                  activeSection === section.id
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
                onClick={() => setActiveSection(section.id)}
              >
                <section.icon
                  className={`mr-3 h-5 w-5 ${
                    activeSection === section.id ? 'text-blue-500' : 'text-gray-400'
                  }`}
                />
                {section.title}
              </button>
            ))}
          </nav>
        </div>

        <div className="lg:col-span-3">
          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              {activeSection === 'notifications' && (
                <div className="space-y-6">
                  <h2 className="text-lg font-medium text-gray-900">Notification Settings</h2>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="text-sm font-medium text-gray-700">
                          Email Notifications
                        </label>
                        <p className="text-sm text-gray-500">
                          Receive alerts via email
                        </p>
                      </div>
                      <button className="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent bg-gray-200 transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2">
                        <span className="translate-x-0 pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out" />
                      </button>
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="text-sm font-medium text-gray-700">
                          Push Notifications
                        </label>
                        <p className="text-sm text-gray-500">
                          Receive alerts on your mobile device
                        </p>
                      </div>
                      <button className="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent bg-blue-500 transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2">
                        <span className="translate-x-5 pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out" />
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {activeSection === 'cameras' && (
                <div className="space-y-6">
                  <h2 className="text-lg font-medium text-gray-900">Camera Settings</h2>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Detection Sensitivity
                      </label>
                      <select className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500">
                        <option>High</option>
                        <option>Medium</option>
                        <option>Low</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Recording Quality
                      </label>
                      <select className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500">
                        <option>4K</option>
                        <option>1080p</option>
                        <option>720p</option>
                      </select>
                    </div>
                  </div>
                </div>
              )}

              {activeSection === 'security' && (
                <div className="space-y-6">
                  <h2 className="text-lg font-medium text-gray-900">Security Rules</h2>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Alert Threshold
                      </label>
                      <input
                        type="number"
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                        placeholder="Enter confidence threshold (0-100)"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Response Time
                      </label>
                      <select className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500">
                        <option>Immediate</option>
                        <option>5 minutes</option>
                        <option>15 minutes</option>
                        <option>30 minutes</option>
                      </select>
                    </div>
                  </div>
                </div>
              )}

              {activeSection === 'users' && (
                <div className="space-y-6">
                  <h2 className="text-lg font-medium text-gray-900">User Management</h2>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Default User Role
                      </label>
                      <select className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500">
                        <option>Admin</option>
                        <option>Security</option>
                        <option>Staff</option>
                        <option>Viewer</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Session Timeout
                      </label>
                      <select className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500">
                        <option>15 minutes</option>
                        <option>30 minutes</option>
                        <option>1 hour</option>
                        <option>4 hours</option>
                      </select>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 