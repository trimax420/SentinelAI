"use client";

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';

interface FootfallApiResponseItem {
  timestamp_hour: string;
  unique_person_count: number;
  camera_id: string; // Add camera_id based on backend model
}

interface FootfallData {
  timestamp_hour: string;
  unique_person_count: number;
}

export default function FootfallChart() {
  const [data, setData] = useState<FootfallData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const today = new Date();
        const startTime = new Date(today.getFullYear(), today.getMonth(), today.getDate(), 0, 0, 0).toISOString();
        const endTime = new Date(today.getFullYear(), today.getMonth(), today.getDate(), 23, 59, 59, 999).toISOString();

        const response: FootfallApiResponseItem[] = await api.getHourlyFootfall({ start_time: startTime, end_time: endTime });
        
        // Aggregate data across all cameras
        const aggregatedData: { [hour: string]: number } = {};
        response.forEach((item: FootfallApiResponseItem) => { // Explicit type for item
          const hour = new Date(item.timestamp_hour).getHours();
          const hourKey = `${String(hour).padStart(2, '0')}:00`;
          aggregatedData[hourKey] = (aggregatedData[hourKey] || 0) + item.unique_person_count;
        });

        const formattedData = Object.entries(aggregatedData)
          .map(([hour, count]) => ({ timestamp_hour: hour, unique_person_count: count }))
          .sort((a, b) => a.timestamp_hour.localeCompare(b.timestamp_hour)); // Sort by hour

        setData(formattedData);
        setError(null);
      } catch (err) {
        console.error("Failed to fetch footfall data:", err);
        setError("Failed to load footfall data.");
      }
      setLoading(false);
    };
    fetchData();
  }, []);

  const formatXAxis = (tickItem: string) => {
     // Show only every few hours to prevent clutter
     const hour = parseInt(tickItem.split(':')[0], 10);
     return hour % 3 === 0 ? tickItem : ''; 
  };

  return (
    <Card>
      <CardHeader>
        <h3 className="text-lg font-semibold">Hourly Footfall (Today)</h3>
      </CardHeader>
      <CardContent style={{ height: '300px' }}> {/* Ensure height for ResponsiveContainer */}
        {loading && <div className="text-center">Loading...</div>}
        {error && <div className="text-center text-red-500">{error}</div>}
        {!loading && !error && data.length > 0 && (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="colorFootfall" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#8884d8" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp_hour" tickFormatter={formatXAxis} />
              <YAxis />
              <Tooltip />
              <Area 
                type="monotone" 
                dataKey="unique_person_count" 
                stroke="#8884d8" 
                fillOpacity={1} 
                fill="url(#colorFootfall)" 
                name="Footfall"
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
        {!loading && !error && data.length === 0 && (
           <div className="text-center text-gray-500">No footfall data available for today.</div>
        )}
      </CardContent>
    </Card>
  );
} 