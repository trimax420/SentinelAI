"use client";

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend } from 'recharts';

interface DemographicsApiResponseItem {
  camera_id: string;
  timestamp_hour: string;
  demographics_data: { [category: string]: number } | null;
}

interface DemographicsData {
  name: string; // e.g., "male_adult"
  value: number; // count
}

// Define colors for consistency
const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d', '#ffc658', '#d0ed57'];

export default function DemographicsChart() {
  const [data, setData] = useState<DemographicsData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const today = new Date();
        const startTime = new Date(today.getFullYear(), today.getMonth(), today.getDate(), 0, 0, 0).toISOString();
        const endTime = new Date(today.getFullYear(), today.getMonth(), today.getDate(), 23, 59, 59, 999).toISOString();

        const response: DemographicsApiResponseItem[] = await api.getHourlyDemographics({ start_time: startTime, end_time: endTime });

        // Aggregate data across all cameras and hours for today
        const aggregatedData: { [category: string]: number } = {};
        response.forEach((item: DemographicsApiResponseItem) => {
          if (item.demographics_data && typeof item.demographics_data === 'object') {
            Object.entries(item.demographics_data).forEach(([category, count]) => {
              aggregatedData[category] = (aggregatedData[category] || 0) + Number(count || 0);
            });
          }
        });

        const formattedData = Object.entries(aggregatedData)
          .map(([name, value]) => ({ name: name.replace('_', ' '), value })) // Format name
          .sort((a, b) => b.value - a.value); // Sort descending by count

        setData(formattedData);
        setError(null);
      } catch (err) {
        console.error("Failed to fetch demographics data:", err);
        setError("Failed to load demographics data.");
      }
      setLoading(false);
    };
    fetchData();
  }, []);

  return (
    <Card>
      <CardHeader>
        <h3 className="text-lg font-semibold">Customer Demographics (Today)</h3>
      </CardHeader>
      <CardContent style={{ height: '300px' }}>
        {loading && <div className="text-center">Loading...</div>}
        {error && <div className="text-center text-red-500">{error}</div>}
        {!loading && !error && data.length > 0 && (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                labelLine={false}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
                nameKey="name"
                label={({ cx, cy, midAngle, innerRadius, outerRadius, percent, index }) => {
                  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
                  const x = cx + radius * Math.cos(-midAngle * Math.PI / 180);
                  const y = cy + radius * Math.sin(-midAngle * Math.PI / 180);
                  return (
                    <text x={x} y={y} fill="white" textAnchor={x > cx ? 'start' : 'end'} dominantBaseline="central">
                      {`${(percent * 100).toFixed(0)}%`}
                    </text>
                  );
                }}
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        )}
        {!loading && !error && data.length === 0 && (
           <div className="text-center text-gray-500">No demographics data available for today.</div>
        )}
      </CardContent>
    </Card>
  );
} 