"use client";

import React, { useEffect, useState } from 'react';
import { api, type Alert } from '@/lib/api';
import { AlertTriangle, TrendingUp, Map } from 'lucide-react';
import Image from 'next/image';

interface AlertCardProps {
  alert: Alert;
}

const AlertCard: React.FC<AlertCardProps> = ({ alert }) => {
  const getSeverityBadge = (severity: number) => {
    switch (severity) {
      case 3:
        return <span className="px-2 py-1 text-xs rounded-full bg-red-100 text-red-600">high</span>;
      case 2:
        return <span className="px-2 py-1 text-xs rounded-full bg-yellow-100 text-yellow-600">medium</span>;
      default:
        return <span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-600">low</span>;
    }
  };

  const formatTime = (date: Date) => {
    return new Date(date).toLocaleTimeString('en-US', {
      hour12: true,
      hour: 'numeric',
      minute: '2-digit',
      timeZone: 'UTC'
    }).toUpperCase();
  };

  return (
    <div className="bg-white rounded-lg shadow-sm overflow-hidden">
      <div className="relative">
        {alert.snapshot_path ? (
          <Image
            src={alert.snapshot_path}
            alt={alert.alert_type}
            width={400}
            height={200}
            className="w-full h-48 object-cover"
          />
        ) : (
          <div className="w-full h-48 bg-gray-100 flex items-center justify-center">
            <AlertTriangle className="w-12 h-12 text-gray-400" />
          </div>
        )}
        <div className="absolute top-2 left-2">
          <span className="px-2 py-1 text-xs bg-blue-500 text-white rounded-full">New</span>
        </div>
        <div className="absolute top-2 right-2">
          {getSeverityBadge(alert.severity)}
        </div>
        <div className="absolute bottom-2 left-2 bg-gray-900 bg-opacity-75 px-2 py-1 rounded">
          <span className="text-xs text-white">{alert.alert_type} Detection</span>
        </div>
      </div>
      <div className="p-4">
        <div className="flex justify-between items-center mb-2">
          <h3 className="text-lg font-semibold capitalize">{alert.alert_type}</h3>
          <span className="text-sm text-gray-500">{formatTime(alert.timestamp)}</span>
        </div>
        <p className="text-gray-600 mb-2">{alert.location || 'Unknown Location'}</p>
        <p className="text-sm text-gray-500">{alert.description}</p>
        <div className="mt-4">
          <button className="text-blue-500 text-sm font-medium hover:text-blue-600">
            View Details
          </button>
        </div>
      </div>
    </div>
  );
};

const AlertsDashboard: React.FC = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [activeTab, setActiveTab] = useState<'recent' | 'all' | 'trends' | 'heatmap'>('recent');

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const data = await api.getAlerts({ limit: 8 });
        setAlerts(data);
      } catch (error) {
        console.error('Error fetching alerts:', error);
      }
    };

    fetchAlerts();

    // Subscribe to real-time updates
    const unsubscribe = api.subscribeToAlerts((newAlerts) => {
      setAlerts(newAlerts);
    });

    return () => {
      unsubscribe();
    };
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex space-x-4">
        <button
          className={`flex items-center px-4 py-2 rounded-lg ${
            activeTab === 'recent'
              ? 'bg-blue-500 text-white'
              : 'bg-white text-gray-600 hover:bg-gray-50'
          }`}
          onClick={() => setActiveTab('recent')}
        >
          <AlertTriangle className="w-5 h-5 mr-2" />
          Recent Alerts
        </button>
        <button
          className={`flex items-center px-4 py-2 rounded-lg ${
            activeTab === 'all'
              ? 'bg-blue-500 text-white'
              : 'bg-white text-gray-600 hover:bg-gray-50'
          }`}
          onClick={() => setActiveTab('all')}
        >
          All Alerts
        </button>
        <button
          className={`flex items-center px-4 py-2 rounded-lg ${
            activeTab === 'trends'
              ? 'bg-blue-500 text-white'
              : 'bg-white text-gray-600 hover:bg-gray-50'
          }`}
          onClick={() => setActiveTab('trends')}
        >
          <TrendingUp className="w-5 h-5 mr-2" />
          Incident Trends
        </button>
        <button
          className={`flex items-center px-4 py-2 rounded-lg ${
            activeTab === 'heatmap'
              ? 'bg-blue-500 text-white'
              : 'bg-white text-gray-600 hover:bg-gray-50'
          }`}
          onClick={() => setActiveTab('heatmap')}
        >
          <Map className="w-5 h-5 mr-2" />
          Location Heatmap
        </button>
      </div>

      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold">Recent Alerts</h2>
        <p className="text-sm text-gray-500">
          Showing {alerts.length} of {alerts.length} alerts
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {alerts.map((alert) => (
          <AlertCard key={alert.id} alert={alert} />
        ))}
      </div>
    </div>
  );
};

export default AlertsDashboard; 