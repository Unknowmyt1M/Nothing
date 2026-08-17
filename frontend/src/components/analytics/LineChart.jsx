'use client';
import { useState, useMemo } from 'react';

function abbreviateDate(dateStr) {
  const d = new Date(dateStr);
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  return `${months[d.getMonth()]} ${d.getDate()}`;
}

function formatTick(value) {
  if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
  if (value >= 1000) return `${(value / 1000).toFixed(0)}K`;
  return String(value);
}

export default function LineChart({
  data = [],
  color = 'var(--color-cyan)',
  height = 260,
  showDots = true,
  formatValue,
}) {
  const [hoveredIndex, setHoveredIndex] = useState(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  const { pathD, areaD, points, xTicks, yTicks, minY, maxY, svgWidth, padding } = useMemo(() => {
    if (!data.length) return { pathD: '', areaD: '', points: [], xTicks: [], yTicks: [], minY: 0, maxY: 0, svgWidth: 800, padding: { top: 20, right: 20, bottom: 40, left: 60 } };

    const values = data.map((d) => d.value);
    const minV = Math.min(...values);
    const maxV = Math.max(...values);
    const range = maxV - minV || 1;
    const pad = { top: 20, right: 20, bottom: 40, left: 60 };
    const w = 800;
    const h = height;
    const innerW = w - pad.left - pad.right;
    const innerH = h - pad.top - pad.bottom;

    const pts = data.map((d, i) => ({
      x: pad.left + (i / (data.length - 1 || 1)) * innerW,
      y: pad.top + innerH - ((d.value - minV) / range) * innerH,
      value: d.value,
      date: d.date,
    }));

    let smoothPath = '';
    let areaPath = '';
    if (pts.length > 1) {
      smoothPath = `M ${pts[0].x},${pts[0].y}`;
      for (let i = 1; i < pts.length; i++) {
        const prev = pts[i - 1];
        const curr = pts[i];
        const cpx1 = prev.x + (curr.x - prev.x) * 0.4;
        const cpx2 = curr.x - (curr.x - prev.x) * 0.4;
        smoothPath += ` C ${cpx1},${prev.y} ${cpx2},${curr.y} ${curr.x},${curr.y}`;
      }
      areaPath = smoothPath + ` L ${pts[pts.length - 1].x},${pad.top + innerH} L ${pts[0].x},${pad.top + innerH} Z`;
    }

    const xTickCount = Math.min(data.length, 6);
    const xTickStep = Math.max(1, Math.floor(data.length / xTickCount));
    const xT = [];
    for (let i = 0; i < data.length; i += xTickStep) {
      xT.push({ x: pts[i].x, label: abbreviateDate(data[i].date) });
    }

    const yTickCount = 5;
    const yT = [];
    for (let i = 0; i <= yTickCount; i++) {
      const val = minV + (range * i) / yTickCount;
      const yPos = pad.top + innerH - (i / yTickCount) * innerH;
      yT.push({ y: yPos, value: val });
    }

    return {
      pathD: smoothPath,
      areaD: areaPath,
      points: pts,
      xTicks: xT,
      yTicks: yT,
      minY: minV,
      maxY: maxV,
      svgWidth: w,
      padding: pad,
    };
  }, [data, height]);

  const resolveColor = (c) => {
    if (typeof getComputedStyle === 'undefined') return c;
    if (!c.startsWith('var(')) return c;
    const varName = c.replace('var(', '').replace(')', '');
    try {
      return getComputedStyle(document.documentElement).getPropertyValue(varName).trim() || c;
    } catch {
      return c;
    }
  };

  const resolvedColor = resolveColor(color);
  const gradId = `grad-${Math.random().toString(36).slice(2, 9)}`;

  if (!data.length) {
    return (
      <div
        style={{
          height,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--color-text-muted)',
          fontSize: '14px',
        }}
      >
        No data available
      </div>
    );
  }

  return (
    <div style={{ position: 'relative', width: '100%', overflow: 'hidden' }}>
      <svg
        viewBox={`0 0 ${svgWidth} ${height}`}
        style={{ width: '100%', height: `${height}px` }}
        onMouseLeave={() => setHoveredIndex(null)}
      >
        <defs>
          <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={resolvedColor} stopOpacity="0.3" />
            <stop offset="100%" stopColor={resolvedColor} stopOpacity="0" />
          </linearGradient>
        </defs>

        {yTicks.map((tick, i) => (
          <g key={i}>
            <line
              x1={padding.left}
              y1={tick.y}
              x2={svgWidth - padding.right}
              y2={tick.y}
              stroke="rgba(255,255,255,0.05)"
              strokeWidth="1"
            />
            <text
              x={padding.left - 10}
              y={tick.y + 4}
              fill="var(--color-text-muted)"
              fontSize="11"
              fontFamily="var(--font-mono)"
              textAnchor="end"
            >
              {formatTick(tick.value)}
            </text>
          </g>
        ))}

        {xTicks.map((tick, i) => (
          <text
            key={i}
            x={tick.x}
            y={height - 10}
            fill="var(--color-text-muted)"
            fontSize="11"
            fontFamily="var(--font-mono)"
            textAnchor="middle"
          >
            {tick.label}
          </text>
        ))}

        {areaD && (
          <path d={areaD} fill={`url(#${gradId})`} />
        )}

        {pathD && (
          <path
            d={pathD}
            fill="none"
            stroke={resolvedColor}
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        )}

        {showDots && points.map((pt, i) => (
          <circle
            key={i}
            cx={pt.x}
            cy={pt.y}
            r={hoveredIndex === i ? 5 : 3}
            fill={hoveredIndex === i ? resolvedColor : 'var(--bg-card)'}
            stroke={resolvedColor}
            strokeWidth="2"
            style={{ cursor: 'pointer', transition: 'r 0.15s ease' }}
            onMouseEnter={(e) => {
              setHoveredIndex(i);
              const rect = e.target.closest('svg').getBoundingClientRect();
              setTooltipPos({
                x: (pt.x / svgWidth) * rect.width,
                y: (pt.y / height) * rect.height - 10,
              });
            }}
          />
        ))}

        {hoveredIndex != null && (
          <>
            <line
              x1={points[hoveredIndex].x}
              y1={padding.top}
              x2={points[hoveredIndex].x}
              y2={height - padding.bottom}
              stroke="rgba(255,255,255,0.15)"
              strokeWidth="1"
              strokeDasharray="4,4"
            />
          </>
        )}
      </svg>

      {hoveredIndex != null && (
        <div
          style={{
            position: 'absolute',
            left: `${tooltipPos.x}px`,
            top: `${tooltipPos.y}px`,
            transform: 'translate(-50%, -100%)',
            background: 'rgba(10, 8, 28, 0.95)',
            border: '1px solid var(--color-border)',
            borderRadius: '8px',
            padding: '8px 12px',
            pointerEvents: 'none',
            zIndex: 10,
            whiteSpace: 'nowrap',
          }}
        >
          <div
            style={{
              fontSize: '12px',
              fontFamily: 'var(--font-mono)',
              fontWeight: '700',
              color: 'var(--color-text-primary)',
            }}
          >
            {formatValue
              ? formatValue(points[hoveredIndex].value)
              : new Intl.NumberFormat('en-US').format(points[hoveredIndex].value)}
          </div>
          <div
            style={{
              fontSize: '11px',
              color: 'var(--color-text-muted)',
              marginTop: '2px',
            }}
          >
            {abbreviateDate(points[hoveredIndex].date)}
          </div>
        </div>
      )}
    </div>
  );
}
