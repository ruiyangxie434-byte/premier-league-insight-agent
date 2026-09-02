import type { TimelineRoundSnapshot } from "../../types/api";

interface PositionTimelineChartProps {
  rounds: TimelineRoundSnapshot[];
  selectedSlugs: string[];
  currentMatchweek: number;
}

const width = 960;
const height = 420;
const padding = { top: 30, right: 84, bottom: 46, left: 48 };

function readableColor(color: string) {
  const red = Number.parseInt(color.slice(1, 3), 16);
  const green = Number.parseInt(color.slice(3, 5), 16);
  const blue = Number.parseInt(color.slice(5, 7), 16);
  const luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue;
  return luminance < 76 ? "#d9fff0" : color;
}

export function PositionTimelineChart({
  rounds,
  selectedSlugs,
  currentMatchweek,
}: PositionTimelineChartProps) {
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;
  const xFor = (matchweek: number) =>
    padding.left + ((matchweek - 1) / 37) * plotWidth;
  const yFor = (position: number) =>
    padding.top + ((position - 1) / 19) * plotHeight;
  const clubMap = new Map(
    rounds.at(-1)?.rows.map((row) => [row.club.slug, row.club]) ?? [],
  );
  const currentX = xFor(currentMatchweek);
  const yTicks = [1, 4, 8, 12, 16, 18, 20];
  const xTicks = [1, 5, 10, 15, 20, 25, 30, 35, 38];

  return (
    <div className="timeline-chart-wrap">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label={`${selectedSlugs.map((slug) => clubMap.get(slug)?.short_name).filter(Boolean).join("、")}的38轮排名轨迹`}
      >
        <rect
          className="timeline-chart-zone timeline-chart-zone-top"
          x={padding.left}
          y={yFor(1) - 8}
          width={plotWidth}
          height={yFor(4) - yFor(1) + 16}
        />
        <rect
          className="timeline-chart-zone timeline-chart-zone-bottom"
          x={padding.left}
          y={yFor(18) - 8}
          width={plotWidth}
          height={yFor(20) - yFor(18) + 16}
        />

        {yTicks.map((tick) => (
          <g key={tick}>
            <line
              className="timeline-chart-grid"
              x1={padding.left}
              x2={width - padding.right}
              y1={yFor(tick)}
              y2={yFor(tick)}
            />
            <text
              className="timeline-chart-label"
              x={padding.left - 14}
              y={yFor(tick) + 4}
              textAnchor="end"
            >
              {tick}
            </text>
          </g>
        ))}
        {xTicks.map((tick) => (
          <text
            className="timeline-chart-label"
            key={tick}
            x={xFor(tick)}
            y={height - 15}
            textAnchor="middle"
          >
            MW {tick}
          </text>
        ))}

        <line
          className="timeline-chart-current"
          x1={currentX}
          x2={currentX}
          y1={padding.top - 12}
          y2={height - padding.bottom + 8}
        />
        <text
          className="timeline-chart-current-label"
          x={currentX}
          y={17}
          textAnchor="middle"
        >
          MW {currentMatchweek}
        </text>

        {selectedSlugs.map((slug) => {
          const club = clubMap.get(slug);
          if (!club) {
            return null;
          }
          const color = readableColor(club.primary_color);
          const rows = rounds
            .map((round) => round.rows.find((row) => row.club.slug === slug))
            .filter((row) => row !== undefined);
          const points = rows
            .map((row) => `${xFor(row.matchweek)},${yFor(row.position)}`)
            .join(" ");
          const current = rows[currentMatchweek - 1];
          const final = rows.at(-1);
          return (
            <g key={slug}>
              <polyline
                className="timeline-chart-line"
                points={points}
                stroke={color}
              />
              {current && (
                <circle
                  className="timeline-chart-focus"
                  cx={xFor(current.matchweek)}
                  cy={yFor(current.position)}
                  fill={color}
                  r="6"
                />
              )}
              {final && (
                <text
                  className="timeline-chart-club-label"
                  fill={color}
                  x={width - padding.right + 10}
                  y={yFor(final.position) + 4}
                >
                  {club.short_name}
                </text>
              )}
            </g>
          );
        })}
      </svg>
      <div className="timeline-chart-legend" aria-hidden="true">
        {selectedSlugs.map((slug) => {
          const club = clubMap.get(slug);
          const current = rounds[currentMatchweek - 1]?.rows.find(
            (row) => row.club.slug === slug,
          );
          if (!club || !current) {
            return null;
          }
          return (
            <span key={slug}>
              <i style={{ background: readableColor(club.primary_color) }} />
              {club.short_name} · 第 {current.position} · {current.points} 分
            </span>
          );
        })}
      </div>
    </div>
  );
}
