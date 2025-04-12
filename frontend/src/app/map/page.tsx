"use client";

import StoreMap from '@/components/security/StoreMap';
import { useState } from 'react';
import { MapPin, Users, AlertTriangle } from 'lucide-react';

interface ZoneStats {
  id: string;
  name: string;
  type: string;
  peopleCount: number;
  alertCount: number;
}

const zoneStats: ZoneStats[] = [
  {
    id: '1',
    name: 'Perfume Section',
    type: 'perfume',
    peopleCount: 12,
    alertCount: 2,
  },
  {
    id: '2',
    name: 'Jewelry Section',
    type: 'jewelry',
    peopleCount: 8,
    alertCount: 1,
  },
  {
    id: '3',
    name: 'Electronics Section',
    type: 'electronics',
    peopleCount: 15,
    alertCount: 0,
  },
  {
    id: '4',
    name: 'General Area',
    type: 'general',
    peopleCount: 25,
    alertCount: 0,
  },
];

export default function MapPage() {
  const [selectedZone, setSelectedZone] = useState<string | null>(null);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold text-gray-900">Store Map</h1>
        <div className="flex space-x-4">
          <button className="bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600">
            Export Map Data
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3">
          <StoreMap />
        </div>
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Zone Statistics</h2>
            <div className="space-y-4">
              {zoneStats.map((zone) => (
                <div
                  key={zone.id}
                  className={`p-4 rounded-lg border-2 ${
                    selectedZone === zone.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200'
                  } cursor-pointer`}
                  onClick={() => setSelectedZone(zone.id)}
                >
                  <div className="flex justify-between items-center">
                    <h3 className="text-sm font-medium text-gray-900">{zone.name}</h3>
                    <span className="text-xs text-gray-500">{zone.type}</span>
                  </div>
                  <div className="mt-2 flex items-center space-x-4">
                    <div className="flex items-center text-sm text-gray-500">
                      <Users className="h-4 w-4 mr-1" />
                      {zone.peopleCount} people
                    </div>
                    <div className="flex items-center text-sm text-gray-500">
                      <AlertTriangle className="h-4 w-4 mr-1" />
                      {zone.alertCount} alerts
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
            <div className="space-y-4">
              <button className="w-full bg-gray-100 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-200">
                View All Alerts
              </button>
              <button className="w-full bg-gray-100 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-200">
                Generate Report
              </button>
              <button className="w-full bg-gray-100 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-200">
                Configure Zones
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 