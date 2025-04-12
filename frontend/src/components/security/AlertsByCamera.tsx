"use client";

import React, { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface AlertData {
  camera_id: string;
  camera_name: string;
  high: number;
  medium: number;
  total: number;
}

interface AlertsByCameraProps {
  className?: string;
}

const AlertsByCamera: React.FC<AlertsByCameraProps> = ({ className }) => {
  const [alertsData, setAlertsData] = useState<AlertData[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAlertsByCameraData = async () => {
      try {
        setLoading(true);
        // Fetch alerts
        const alertsResponse = await fetch('/api/alerts/');
        if (!alertsResponse.ok) {
          throw new Error('Failed to fetch alerts');
        }
        
        const alertsData = await alertsResponse.json();
        
        // Fetch cameras to get their names
        const camerasResponse = await fetch('/api/live-cameras/status/');
        if (!camerasResponse.ok) {
          throw new Error('Failed to fetch camera data');
        }
        
        const camerasData = await camerasResponse.json();
        
        // Initialize empty counts for all cameras with severity levels
        const alertsByCameraMap = new Map<string, { high: number, medium: number, total: number }>();
        
        // Initialize with zero counts for all cameras
        Object.keys(camerasData).forEach(cameraId => {
          alertsByCameraMap.set(cameraId, { high: 0, medium: 0, total: 0 });
        });
        
        // Count alerts by camera and severity
        alertsData.forEach((alert: any) => {
          const cameraId = alert.camera_id || extractCameraId(alert.description);
          if (!cameraId) return;
          
          const data = alertsByCameraMap.get(cameraId) || { high: 0, medium: 0, total: 0 };
          
          // Map severity to category:
          // severity 3: high, severity 2: medium
          if (alert.severity === 3) {
            data.high += 1;
          } else if (alert.severity === 2) {
            data.medium += 1;
          }
          
          // Only increment total if it's a severity we're tracking
          if (alert.severity === 2 || alert.severity === 3) {
            data.total += 1;
          }
          
          alertsByCameraMap.set(cameraId, data);
        });
        
        // Transform to array format for the chart
        const formattedData = Array.from(alertsByCameraMap.entries())
          .map(([camera_id, counts]) => ({
            camera_id,
            camera_name: camerasData[camera_id]?.zone_name || camera_id,
            high: counts.high,
            medium: counts.medium,
            total: counts.total
          }))
          .filter(item => item.total > 0) // Only show cameras with alerts
          .sort((a, b) => b.total - a.total); // Sort by total count descending
        
        setAlertsData(formattedData);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching alerts by camera data:', error);
        setError('Failed to load alerts data');
        setLoading(false);
      }
    };

    fetchAlertsByCameraData();
    // Update data every 30 seconds
    const intervalId = setInterval(fetchAlertsByCameraData, 30000);
    
    return () => clearInterval(intervalId);
  }, []);

  // Helper function to extract camera ID from alert description
  const extractCameraId = (description: string): string | null => {
    if (!description) return null;
    
    // Pattern: "cam001:", "cam002:", etc.
    const match = description.match(/^(cam\d+):/i);
    return match ? match[1] : null;
  };

  if (loading) {
    return (
      <div className={`bg-white rounded-lg p-4 ${className} flex items-center justify-center h-64`}>
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-white rounded-lg p-4 ${className} flex items-center justify-center h-64`}>
        <p className="text-red-500">{error}</p>
      </div>
    );
  }

  if (alertsData.length === 0) {
    return (
      <div className={`bg-white rounded-lg p-4 ${className} flex items-center justify-center h-64`}>
        <p className="text-gray-500">No alerts found</p>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg p-4 ${className}`}>
      <h2 className="text-lg font-semibold mb-4">Alerts by Camera & Severity</h2>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={alertsData}
            margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="camera_name" />
            <YAxis />
            <Tooltip 
              formatter={(value: number, name: string) => {
                const formattedName = name === 'high' ? 'High Severity' : 
                                      name === 'medium' ? 'Medium Severity' : name;
                return [value, formattedName];
              }}
              labelFormatter={(value: string) => `Camera: ${value}`}
            />
            <Legend formatter={(value) => {
              return value === 'high' ? 'High Severity' : 
                     value === 'medium' ? 'Medium Severity' : value;
            }} />
            <Bar dataKey="high" name="high" stackId="a" fill="#EF4444" barSize={40} /> {/* Red for high */}
            <Bar dataKey="medium" name="medium" stackId="a" fill="#F59E0B" barSize={40} /> {/* Amber for medium */}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default AlertsByCamera; 