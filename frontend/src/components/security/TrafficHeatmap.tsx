"use client";

import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface TrafficData {
  hour: string;
  count: number;
}

export default function TrafficHeatmap() {
  const [trafficData, setTrafficData] = useState<TrafficData[]>([]);

  useEffect(() => {
    // Simulated API call for traffic data
    const fetchTrafficData = () => {
      // Mock data - in real app, this would be an API call
      const mockData: TrafficData[] = [
        { hour: '00:00', count: 5 },
        { hour: '01:00', count: 3 },
        { hour: '02:00', count: 2 },
        { hour: '03:00', count: 1 },
        { hour: '04:00', count: 2 },
        { hour: '05:00', count: 4 },
        { hour: '06:00', count: 8 },
        { hour: '07:00', count: 12 },
        { hour: '08:00', count: 15 },
        { hour: '09:00', count: 20 },
        { hour: '10:00', count: 25 },
        { hour: '11:00', count: 30 },
        { hour: '12:00', count: 35 },
        { hour: '13:00', count: 32 },
        { hour: '14:00', count: 28 },
        { hour: '15:00', count: 25 },
        { hour: '16:00', count: 22 },
        { hour: '17:00', count: 20 },
        { hour: '18:00', count: 18 },
        { hour: '19:00', count: 15 },
        { hour: '20:00', count: 12 },
        { hour: '21:00', count: 8 },
        { hour: '22:00', count: 6 },
        { hour: '23:00', count: 4 },
      ];
      setTrafficData(mockData);
    };

    fetchTrafficData();
    const interval = setInterval(fetchTrafficData, 300000); // Update every 5 minutes

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Store Traffic Pattern</h2>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={trafficData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="hour"
              angle={-45}
              textAnchor="end"
              height={60}
              interval={2}
            />
            <YAxis />
            <Tooltip />
            <Bar
              dataKey="count"
              fill="#3B82F6"
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
} 