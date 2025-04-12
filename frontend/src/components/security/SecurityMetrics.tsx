"use client";

import React, { useEffect, useState } from 'react';
import { Camera, Users, AlertTriangle, Activity } from 'lucide-react';
import { api, type Analytics } from '@/lib/api';

interface MetricCardProps {
  title: string;
  value: string | number;
  change?: number;
  icon: React.ReactNode;
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, change, icon }) => (
  <div className="bg-white rounded-lg shadow p-6">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm font-medium text-gray-600">{title}</p>
        <p className="text-2xl font-semibold mt-1">{value}</p>
        {change !== undefined && (
          <p className={`text-sm mt-1 ${change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {change >= 0 ? '↑' : '↓'} {Math.abs(change)}%
          </p>
        )}
      </div>
      <div className="p-3 bg-blue-50 rounded-full">
        {icon}
      </div>
    </div>
  </div>
);

const SecurityMetrics: React.FC = () => {
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [cameras, setCameras] = useState<number>(0);
  const [alerts, setAlerts] = useState<number>(0);
  const [previousAnalytics, setPreviousAnalytics] = useState<Analytics | null>(null);

  useEffect(() => {
    // Fetch initial data
    const fetchData = async () => {
      try {
        const [currentAnalytics, camerasData, alertsData, previousAnalyticsData] = await Promise.all([
          api.getCurrentAnalytics(),
          api.getCameras(),
          api.getAlerts({ limit: 1 }),
          api.getAnalytics({ limit: 2 })
        ]);

        setAnalytics(currentAnalytics);
        setCameras(camerasData.length);
        setAlerts(alertsData.length);
        setPreviousAnalytics(previousAnalyticsData[1] || null);
      } catch (error) {
        console.error('Error fetching metrics:', error);
      }
    };

    fetchData();

    // Subscribe to real-time updates
    const unsubscribe = api.subscribeToAnalytics((newAnalytics) => {
      setAnalytics(newAnalytics);
    });

    return () => {
      unsubscribe();
    };
  }, []);

  const calculateChange = (current: number | undefined, previous: number | undefined) => {
    if (current === undefined || previous === undefined || previous === 0) return 0;
    return Math.round(((current - previous) / previous) * 100);
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <MetricCard
        title="Active Cameras"
        value={cameras}
        icon={<Camera className="w-6 h-6 text-blue-600" />}
      />
      <MetricCard
        title="People Detected"
        value={analytics?.person_count || 0}
        change={calculateChange(analytics?.person_count, previousAnalytics?.person_count)}
        icon={<Users className="w-6 h-6 text-blue-600" />}
      />
      <MetricCard
        title="Active Alerts"
        value={alerts}
        icon={<AlertTriangle className="w-6 h-6 text-blue-600" />}
      />
      <MetricCard
        title="Detection Rate"
        value={`${analytics?.suspicious_activity_count || 0}/hr`}
        icon={<Activity className="w-6 h-6 text-blue-600" />}
      />
    </div>
  );
};

export default SecurityMetrics; 