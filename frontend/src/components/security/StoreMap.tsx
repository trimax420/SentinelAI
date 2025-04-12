"use client";

import React, { useEffect, useState } from 'react';
import { api, Analytics } from '@/lib/api';

interface Zone {
  id: string;
  name: string;
  coordinates: number[][];
  analytics: Analytics;
}

const StoreMap: React.FC = () => {
  const [zones, setZones] = useState<Zone[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchZones = async () => {
      try {
        setIsLoading(true);
        const analytics = await api.getCurrentAnalytics();
        // Transform analytics data into zones
        const transformedZones = Object.entries(analytics).map(([id, data]) => ({
          id,
          name: `Zone ${id}`,
          coordinates: [], // This would come from a separate API call in a real app
          analytics: data
        }));
        setZones(transformedZones);
        setError(null);
      } catch (err) {
        setError('Failed to load zone data');
        console.error('Error fetching zones:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchZones();

    // Subscribe to real-time updates
    const unsubscribe = api.subscribeToAnalytics((newAnalytics) => {
      setZones(prevZones => 
        prevZones.map(zone => ({
          ...zone,
          analytics: newAnalytics[zone.id] || zone.analytics
        }))
      );
    });

    return () => {
      unsubscribe();
    };
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-100 rounded-lg">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-96 bg-red-50 rounded-lg">
        <p className="text-red-600">{error}</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h2 className="text-lg font-semibold mb-4">Store Layout</h2>
      <div className="relative h-80 bg-gray-100 rounded-lg">
        {/* This would be a real map component in production */}
        <div className="absolute inset-0 flex items-center justify-center">
          <p className="text-gray-500">Store Map Visualization</p>
        </div>
        
        {/* Zone overlays */}
        {zones.map((zone) => (
          <div
            key={zone.id}
            className="absolute border-2 border-blue-500"
            style={{
              // This would use real coordinates in production
              left: '10%',
              top: '10%',
              width: '80%',
              height: '80%',
            }}
          >
            <div className="absolute -top-6 left-0 bg-blue-500 text-white text-xs px-2 py-1 rounded">
              {zone.name}
            </div>
            <div className="absolute bottom-0 left-0 right-0 bg-white bg-opacity-90 p-2 text-xs">
              <div>People: {zone.analytics.person_count}</div>
              <div>Staff: {zone.analytics.staff_count || 0}</div>
              <div>Customers: {zone.analytics.customer_count || 0}</div>
              <div>Suspicious Activity: {zone.analytics.suspicious_activity_count || 0}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default StoreMap; 