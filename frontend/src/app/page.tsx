"use client"

import React, { useEffect, useState } from 'react';
import { Camera, Users, AlertTriangle } from 'lucide-react';
import { api } from '@/lib/api';
import AlertsPanel from '@/components/security/AlertsPanel';
import AlertsByCamera from '@/components/security/AlertsByCamera';
import AlertsTimeline from '@/components/security/AlertsTimeline';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, ResponsiveContainer } from 'recharts';
import SecurityMetrics from '@/components/security/SecurityMetrics';
import TrafficHeatmap from '@/components/security/TrafficHeatmap';
import StoreMap from '@/components/security/StoreMap';
import FootfallChart from '@/components/security/FootfallChart';
import DemographicsChart from '@/components/security/DemographicsChart';

interface MetricCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
}

interface ZoneAnalytics {
  camera_id: number;
  zone_occupancy: Record<string, number>;
  total_entries: number;
}

interface AnalyticsData {
  total_people: number;
  zone_analytics: ZoneAnalytics[];
}

interface TrafficEntry {
  timestamp: string;
  count: number;
}

interface TrafficSummary {
  hourly_data: TrafficEntry[];
  total_entries: number;
  peak_hour: string;
}

interface Alert {
  id: number;
  timestamp: string;
  alert_type: string;
  severity: number;
  description: string;
  acknowledged: boolean;
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, icon }) => (
  <div className="bg-white rounded-lg shadow p-6">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm font-medium text-gray-600">{title}</p>
        <p className="text-2xl font-semibold mt-1">{value}</p>
      </div>
      <div className="p-3 bg-blue-50 rounded-full">
        {icon}
      </div>
    </div>
  </div>
);

export default function DashboardPage() {
  const [cameras, setCameras] = useState<any[]>([]);
  const [metrics, setMetrics] = useState({
    activeCameras: 0,
    totalPeople: 0,
    activeAlerts: 0
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch cameras using the live-cameras/status endpoint
        const cameraResponse = await fetch('/api/live-cameras/status/');
        if (!cameraResponse.ok) {
          throw new Error('Failed to fetch camera status');
        }
        
        const cameraData = await cameraResponse.json();
        console.log('Camera data from API:', cameraData);
        
        // Transform the camera data from object to array format
        const camerasArray = Object.entries(cameraData).map(([id, info]: [string, any]) => ({
          camera_id: id, // Use camera_id instead of id
          name: info.zone_name || id,
          status: info.status === 'running' ? 'online' : 'offline'
        }));
        
        console.log('Transformed camera array:', camerasArray);
        setCameras(camerasArray);
        setMetrics(prev => ({ ...prev, activeCameras: camerasArray.filter(c => c.status === 'online').length }));

        // Fetch total people count across all cameras
        try {
          const analyticsResponse = await fetch('/api/analytics/current/');
          if (analyticsResponse.ok) {
            const analyticsData = await analyticsResponse.json();
            console.log('Analytics data:', analyticsData);
            
            // Use total_people from the analytics data
            const totalPeople = analyticsData.totalPeople || analyticsData.total_people || 0;
            setMetrics(prev => ({ ...prev, totalPeople }));
          }
        } catch (error) {
          console.error('Error fetching analytics data:', error);
        }

        // Fetch active alerts - using the correct API path
        const alertsResponse = await fetch('/api/alerts/?acknowledged=false');
        if (alertsResponse.ok) {
          const alertsData = await alertsResponse.json();
          console.log('Alerts data:', alertsData);
          setMetrics(prev => ({ ...prev, activeAlerts: alertsData.length }));
        }
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      }
    };

    fetchData();

    // Set up real-time updates
    const intervalId = setInterval(fetchData, 10000); // Update every 10 seconds

    return () => {
      clearInterval(intervalId);
    };
  }, []); // Remove selectedCamera dependency since we're no longer using it

  return (
    <div className="space-y-6 p-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <MetricCard
          title="Active Cameras"
          value={metrics.activeCameras}
          icon={<Camera className="w-6 h-6 text-blue-600" />}
        />
        <MetricCard
          title="People Detected"
          value={metrics.totalPeople}
          icon={<Users className="w-6 h-6 text-blue-600" />}
        />
        <MetricCard
          title="Active Alerts"
          value={metrics.activeAlerts}
          icon={<AlertTriangle className="w-6 h-6 text-blue-600" />}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-6">
          <FootfallChart />
          <DemographicsChart />
        </div>
        <div className="lg:col-span-2 space-y-6">
          <AlertsPanel />
          <AlertsTimeline />
        </div>
      </div>
    </div>
  );
}