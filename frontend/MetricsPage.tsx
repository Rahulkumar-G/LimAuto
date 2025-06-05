import React from 'react';
import {
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

// Step 1: Define interfaces describing the expected metrics data
export interface SuccessFailureDatum {
  status: 'success' | 'failure';
  count: number;
}

export interface TrendPoint {
  time: string; // ISO timestamp or HH:MM label
  success: number;
  failure: number;
}

export interface MetricsProps {
  pieData: SuccessFailureDatum[];
  trendData: TrendPoint[];
}

// Step 2: Build the metrics page component
export const MetricsPage: React.FC<MetricsProps> = ({ pieData, trendData }) => {
  const colors = ['#00C49F', '#FF8042'];
  return (
    <div style={{ width: '100%', height: 400 }}>
      {/* Step 3: Visualize aggregated results with a pie chart */}
      <ResponsiveContainer width="100%" height={200}>
        <PieChart>
          <Pie data={pieData} dataKey="count" nameKey="status" cx="50%" cy="50%" outerRadius={80}>
            {pieData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
            ))}
          </Pie>
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>

      {/* Step 4: Display the 24 h trend with an area chart */}
      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={trendData} stackOffset="expand">
          <XAxis dataKey="time" />
          <YAxis />
          <Tooltip />
          <Area type="monotone" dataKey="success" stackId="1" stroke="#00C49F" fill="#00C49F" />
          <Area type="monotone" dataKey="failure" stackId="1" stroke="#FF8042" fill="#FF8042" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

export default MetricsPage;
