"use client";

import React, { useEffect, useState } from 'react';
import { X, AlertTriangle } from 'lucide-react';
import { api } from '@/lib/api';
import type { Alert } from '@/lib/api';

const AlertsPanel: React.FC = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const getAlertColor = (severity: number) => {
    switch (severity) {
      case 3:
        return 'bg-red-50 border-red-500';
      case 2:
        return 'bg-yellow-50 border-yellow-500';
      default:
        return 'bg-blue-50 border-blue-500';
    }
  };

  const getAlertTitle = (alertType: string): string => {
    switch (alertType) {
      case 'suspicious_pose':
        return 'Suspicious Posture';
      case 'loitering':
        return 'Loitering Detected';
      default:
        return alertType.replace('_', ' ');
    }
  };

  const dismissAlert = async (alertId: number) => {
    try {
      await api.acknowledgeAlert(alertId);
      setAlerts(alerts.filter(alert => alert.id !== alertId));
    } catch (error) {
      console.error('Error dismissing alert:', error);
    }
  };

  useEffect(() => {
    const fetchAlerts = async () => {
      setLoading(true);
      try {
        // Get today's date boundaries
        const today = new Date();
        const startTime = new Date(today.getFullYear(), today.getMonth(), today.getDate(), 0, 0, 0).toISOString();
        const endTime = new Date(today.getFullYear(), today.getMonth(), today.getDate(), 23, 59, 59, 999).toISOString();

        const data = await api.getAlerts({
          acknowledged: false,
          limit: 5, // Limit the panel to top 5 recent alerts
          start_time: startTime,
          end_time: endTime
        });
        setAlerts(data);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch alerts for panel:', err);
        setError('Failed to load recent alerts.');
      }
      setLoading(false);
    };

    fetchAlerts();

    // Set up WebSocket listener
    // Assume callback receives single Alert, handle defensively
    const unsubscribe = api.subscribeToAlerts((newAlert: Alert | Alert[]) => {
      // Defensively handle if it's an array, though unlikely based on previous fixes
      const alertsToAdd = Array.isArray(newAlert) ? newAlert : [newAlert];

      alertsToAdd.forEach(alert => {
        const alertDate = new Date(alert.timestamp);
        const today = new Date();
        const isToday = alertDate.getFullYear() === today.getFullYear() &&
                      alertDate.getMonth() === today.getMonth() &&
                      alertDate.getDate() === today.getDate();
  
        if (!alert.acknowledged && isToday) {
          setAlerts((prevAlerts) => {
            // Avoid duplicates and keep list size limited to 5
            if (!prevAlerts.some(a => a.id === alert.id)) {
              return [alert, ...prevAlerts.slice(0, 4)]; // Keep 5 total (1 new + 4 old)
            }
            return prevAlerts;
          });
        }
      })
    });

    return () => unsubscribe(); // Clean up WebSocket subscription

  }, []); // Fetch only on mount

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-4 border-b">
        <h2 className="text-lg font-semibold">Security Alerts</h2>
      </div>
      <div className="divide-y max-h-96 overflow-y-auto">
        {loading && (
          <div className="p-4 text-center text-gray-500">Loading...</div>
        )}
        {!loading && error && (
          <div className="p-4 text-center text-red-500">{error}</div>
        )}
        {!loading && !error && alerts.map((alert) => (
          <div
            key={alert.id}
            className={`p-4 ${getAlertColor(alert.severity)} border-l-4`}
          >
            <div className="flex justify-between items-start">
              <div>
                <div className="flex items-center space-x-2">
                  <h3 className="text-sm font-medium">{getAlertTitle(alert.alert_type)}</h3>
                  <span className="text-xs text-gray-500">
                    {new Date(alert.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <p className="text-xs text-gray-600 mt-1">{alert.description}</p>
                {alert.detection_id && (
                  <p className="text-gray-600">Detection ID: {alert.detection_id}</p>
                )}
                {alert.track_id && (
                  <p className="text-xs text-gray-500">Track ID: {alert.track_id}</p>
                )}
              </div>
              <button
                className="text-gray-400 hover:text-gray-500"
                onClick={() => dismissAlert(alert.id)}
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          </div>
        ))}
        {!loading && !error && alerts.length === 0 && (
          <div className="p-4 text-center text-gray-500">
            No active alerts
          </div>
        )}
      </div>
    </div>
  );
};

export default AlertsPanel; 