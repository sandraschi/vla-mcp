interface Segment {
  index: number;
  timestamp: number;
  event: string;
}

interface Props {
  segments: Segment[];
  duration: number;
  title?: string;
}

// Dark-theme palette for WALL-WM event-joint vocabulary.
const EVENT_COLORS: Record<string, string> = {
  idle: "#475569",
  approaching: "#3b82f6",
  making_contact: "#f59e0b",
  lifting: "#10b981",
  sliding: "#8b5cf6",
  releasing: "#06b6d4",
  colliding: "#ef4444",
  recovering: "#f97316",
};

const FALLBACK = "#6b7280";
const VB_W = 1000;
const BAR_Y = 28;
const BAR_H = 52;

function colorFor(event: string): string {
  return EVENT_COLORS[event] ?? FALLBACK;
}

export default function EventTimeline({ segments, duration, title }: Props) {
  if (!segments || segments.length === 0) {
    return <p className="text-sm text-gray-500">No event segments to display.</p>;
  }

  // End of the last span: use duration if it extends past the last transition.
  const lastTs = segments[segments.length - 1]?.timestamp ?? 0;
  const end = Math.max(duration || 0, lastTs > 0 ? lastTs * 1.15 : segments.length);
  const span0 = end > 0 ? end : 1;

  const spans = segments.map((seg, i) => {
    const start = seg.timestamp ?? i;
    const next = i + 1 < segments.length ? segments[i + 1].timestamp ?? i + 1 : end;
    const x = (start / span0) * VB_W;
    const w = Math.max(2, ((next - start) / span0) * VB_W);
    return { ...seg, x, w };
  });

  const legend = Array.from(new Set(segments.map((s) => s.event)));

  return (
    <div>
      {title && <h3 className="font-semibold mb-2 text-sm">{title}</h3>}
      <svg viewBox={`0 0 ${VB_W} 110`} className="w-full" role="img" aria-label="Event-joint timeline">
        {/* baseline */}
        <line x1={0} y1={BAR_Y + BAR_H + 8} x2={VB_W} y2={BAR_Y + BAR_H + 8} stroke="#374151" strokeWidth={1} />
        {spans.map((s) => (
          <g key={s.index}>
            <rect
              x={s.x}
              y={BAR_Y}
              width={s.w}
              height={BAR_H}
              fill={colorFor(s.event)}
              rx={3}
              opacity={0.9}
            />
            {s.w > 90 && (
              <text
                x={s.x + s.w / 2}
                y={BAR_Y + BAR_H / 2 + 4}
                textAnchor="middle"
                fontSize={13}
                fill="#0b1120"
                fontWeight={600}
              >
                {s.event}
              </text>
            )}
            <text x={s.x + 2} y={BAR_Y - 6} fontSize={11} fill="#9ca3af">
              t={s.timestamp}
            </text>
          </g>
        ))}
        <text x={0} y={BAR_Y + BAR_H + 24} fontSize={11} fill="#6b7280">
          0
        </text>
        <text x={VB_W} y={BAR_Y + BAR_H + 24} fontSize={11} fill="#6b7280" textAnchor="end">
          {end.toFixed(1)}s
        </text>
      </svg>

      <div className="flex flex-wrap gap-3 mt-2">
        {legend.map((ev) => (
          <span key={ev} className="flex items-center gap-1.5 text-xs text-gray-400">
            <span
              className="inline-block w-3 h-3 rounded-sm"
              style={{ backgroundColor: colorFor(ev) }}
            />
            {ev}
          </span>
        ))}
      </div>
      <p className="text-xs text-gray-600 mt-1">
        Semantic event-joints ({segments.length} transitions) — not fixed-time chunks.
      </p>
    </div>
  );
}
