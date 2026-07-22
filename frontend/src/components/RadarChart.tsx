/**
 * CARERadarChart – Recharts RadarChart wrapper for 4 CARE dimensions.
 */
import React from 'react';
import {
  RadarChart as RechartsRadar,
  PolarGrid,
  PolarAngleAxis,
  Radar,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from 'recharts';

interface RadarDataPoint {
  dimension: string;
  [agentName: string]: number | string;
}

interface RadarSeries {
  name: string;
  color: string;
  dataKey: string;
}

interface CARERadarChartProps {
  data: RadarDataPoint[];
  series: RadarSeries[];
  height?: number;
}

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="card-glass p-3 text-xs">
        <p className="text-slate-300 font-semibold mb-1">{payload[0]?.payload?.dimension}</p>
        {payload.map((p: any) => (
          <div key={p.name} className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: p.color }} />
            <span className="text-slate-400">{p.name}:</span>
            <span className="text-slate-100 font-bold">{Number(p.value).toFixed(1)}</span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

const CARERadarChart: React.FC<CARERadarChartProps> = ({ data, series, height = 300 }) => {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsRadar data={data} cx="50%" cy="50%" outerRadius="75%">
        <PolarGrid stroke="#2D3748" />
        <PolarAngleAxis
          dataKey="dimension"
          tick={{ fill: '#94a3b8', fontSize: 11, fontWeight: 600 }}
        />
        <Tooltip content={<CustomTooltip />} />
        {series.length > 1 && (
          <Legend
            wrapperStyle={{ fontSize: '12px', color: '#94a3b8', paddingTop: '8px' }}
          />
        )}
        {series.map((s) => (
          <Radar
            key={s.name}
            name={s.name}
            dataKey={s.dataKey}
            stroke={s.color}
            fill={s.color}
            fillOpacity={0.15}
            strokeWidth={2}
            dot={{ fill: s.color, r: 3 }}
          />
        ))}
      </RechartsRadar>
    </ResponsiveContainer>
  );
};

export default CARERadarChart;
