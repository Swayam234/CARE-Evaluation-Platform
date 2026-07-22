/**
 * LoadingSkeleton – Skeleton placeholders for major card types.
 */
import React from 'react';

export const SkeletonCard: React.FC<{ className?: string }> = ({ className = '' }) => (
  <div className={`card p-5 ${className}`}>
    <div className="skeleton h-4 w-1/3 mb-3" />
    <div className="skeleton h-8 w-1/2 mb-2" />
    <div className="skeleton h-2 w-full" />
  </div>
);

export const SkeletonRow: React.FC = () => (
  <tr>
    {[...Array(6)].map((_, i) => (
      <td key={i} className="px-4 py-3">
        <div className="skeleton h-4 w-full" />
      </td>
    ))}
  </tr>
);

export const SkeletonGauge: React.FC = () => (
  <div className="flex flex-col items-center gap-4 p-6">
    <div className="skeleton w-48 h-24 rounded-full" />
    <div className="skeleton h-4 w-24" />
  </div>
);

export const SkeletonDimensionCards: React.FC = () => (
  <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
    {[...Array(4)].map((_, i) => (
      <SkeletonCard key={i} />
    ))}
  </div>
);

const LoadingSkeleton: React.FC<{ type?: 'dashboard' | 'table' | 'gauge' }> = ({
  type = 'dashboard',
}) => {
  if (type === 'gauge') return <SkeletonGauge />;
  if (type === 'table') {
    return (
      <div className="table-wrapper">
        <table className="table">
          <tbody>
            {[...Array(5)].map((_, i) => (
              <SkeletonRow key={i} />
            ))}
          </tbody>
        </table>
      </div>
    );
  }
  return (
    <div className="space-y-4 animate-pulse">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
      <SkeletonCard className="h-40" />
    </div>
  );
};

export default LoadingSkeleton;
