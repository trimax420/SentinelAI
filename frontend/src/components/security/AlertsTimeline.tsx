"use client";

import React, { useEffect, useState, useMemo } from 'react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { api, Alert } from '@/lib/api';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts';

// Add a custom CardTitle component since it's not exported from card.tsx
const CardTitle: React.FC<React.HTMLAttributes<HTMLHeadingElement>> = ({ className, ...props }) => {
  return (
    <h3
      className={`text-lg font-semibold leading-none tracking-tight ${className}`}
      {...props}
    />
  );
};

export default function AlertsTimeline() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        setLoading(true);
        // Don't specify a limit to fetch all alerts
        const response = await api.getAlerts();
        if (response && Array.isArray(response)) {
          setAlerts(response);
        }
      } catch (error) {
        console.error('Failed to fetch alerts:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAlerts();

    // Custom WebSocket setup instead of using the api.subscribeToAlerts
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws/alerts';
    const ws = new WebSocket(wsUrl);
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        // Handle both array and single alert cases
        if (Array.isArray(data)) {
          setAlerts(prev => [...prev, ...data]);
        } else if (data && typeof data === 'object') {
          setAlerts(prev => [...prev, data]);
        }
      } catch (error) {
        console.error('Error processing alert data:', error);
      }
    };

    return () => {
      ws.close();
    };
  }, []);

  const chartData = useMemo(() => {
    // Group alerts by hour and detection type
    const timeGroups: Record<string, Record<string, number>> = {};
    
    alerts.forEach(alert => {
      const date = new Date(alert.timestamp);
      const hour = date.getHours();
      const timeKey = `${hour}:00`;
      
      if (!timeGroups[timeKey]) {
        timeGroups[timeKey] = {};
      }
      
      if (!timeGroups[timeKey][alert.alert_type]) {
        timeGroups[timeKey][alert.alert_type] = 0;
      }
      
      timeGroups[timeKey][alert.alert_type]++;
    });
    
    // Convert to array format required by Recharts
    return Object.keys(timeGroups)
      .sort((a, b) => {
        const hourA = parseInt(a.split(':')[0]);
        const hourB = parseInt(b.split(':')[0]);
        return hourA - hourB;
      })
      .map(time => {
        return {
          time,
          ...timeGroups[time]
        };
      });
  }, [alerts]);

  // Calculate the summary data for the table - grouped by camera and severity
  const alertSummaryData = useMemo(() => {
    // Create structure to hold camera and severity data
    const summary: Record<string, Record<number, Record<string, number>>> = {};
    
    alerts.forEach(alert => {
      // Use track_id as the camera identifier since Alert doesn't have camera_id
      const cameraId = alert.track_id || 'unknown';
      const severity = alert.severity;
      const alertType = alert.alert_type;
      
      // Initialize nested objects if they don't exist
      if (!summary[cameraId]) {
        summary[cameraId] = {};
      }
      if (!summary[cameraId][severity]) {
        summary[cameraId][severity] = {};
      }
      if (!summary[cameraId][severity][alertType]) {
        summary[cameraId][severity][alertType] = 0;
      }
      
      // Increment the count for this combination
      summary[cameraId][severity][alertType]++;
    });
    
    return summary;
  }, [alerts]);

  // Extract all unique detection types
  const detectionTypes = useMemo(() => {
    const types = new Set<string>();
    alerts.forEach(alert => {
      types.add(alert.alert_type);
    });
    return Array.from(types);
  }, [alerts]);

  // Get all unique camera IDs
  const cameraIds = useMemo(() => {
    return Object.keys(alertSummaryData);
  }, [alertSummaryData]);

  // Define consistent colors for all detection types
  const colorMap: Record<string, string> = {
    // Original colors
    'loitering': '#8884d8',           // Purple
    'intrusion': '#FF5733',           // Orange-Red
    'suspicious_behavior': '#82ca9d', // Light Green
    'violence': '#ff0000',            // Red
    'theft': '#ffc658',               // Light Yellow
    
    // Additional detection types with fixed colors
    'weapon': '#ff6361',              // Coral Red
    'fight': '#bc5090',               // Purple-Pink
    'fall': '#58508d',                // Deep Purple
    'person': '#003f5c',              // Dark Blue
    'face': '#665191',                // Medium Purple
    'car': '#2f4b7c',                 // Navy Blue
    'unauthorized_access': '#a05195', // Medium Pink-Purple
    'abandoned_object': '#d45087',    // Pink
    'camera_tamper': '#f95d6a',       // Salmon
    'crowd': '#ff7c43',               // Orange
  };
  
  // Default colors for any detection type not in the map
  const defaultColors = ['#4e79a7', '#f28e2c', '#e15759', '#76b7b2', '#59a14f'];

  // Map severity to human-readable text and style
  const getSeverityText = (severity: number) => {
    switch (severity) {
      case 1: return { text: 'Low', color: 'bg-blue-100 text-blue-800' };
      case 2: return { text: 'Medium', color: 'bg-yellow-100 text-yellow-800' };
      case 3: return { text: 'High', color: 'bg-red-100 text-red-800' };
      default: return { text: 'Unknown', color: 'bg-gray-100 text-gray-800' };
    }
  };

  return (
    // Fix the whitespace by using full width and removing left margin
    <div className="w-full">
      <Card className="mb-6">
        <CardHeader className="pb-2">
          <CardTitle>Detections Over Time</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center items-center h-64">
              <p>Loading data...</p>
            </div>
          ) : chartData.length === 0 ? (
            <div className="flex justify-center items-center h-64">
              <p>No detection data available</p>
            </div>
          ) : (
            <div className="h-96">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={chartData}
                  margin={{ top: 5, right: 5, left: 5, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis label={{ value: 'Number of Detections', angle: -90, position: 'insideLeft' }} />
                  <Tooltip />
                  <Legend />
                  {detectionTypes.map((type, index) => (
                    <Bar 
                      key={type} 
                      dataKey={type} 
                      stackId="a"
                      name={type.replace(/_/g, ' ')}
                      fill={colorMap[type] || defaultColors[index % defaultColors.length]} 
                    />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Add the table for alerts by camera and severity */}
      
    </div>
  );
} 