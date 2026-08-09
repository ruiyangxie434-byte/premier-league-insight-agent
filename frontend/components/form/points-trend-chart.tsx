import type { SeasonFormClubItem } from "../../types/api";

interface PointsTrendChartProps {
  clubs: SeasonFormClubItem[];
}

const width = 900;
const height = 310;
const padding = { top: 24, right: 30, bottom: 42, left: 48 };

function readableColor(color: string) {
  const red = Number.parseInt(color.slice(1, 3), 16);
  const green = Number.parseInt(color.slice(3, 5), 16);
  const blue = Number.parseInt(color.slice(5, 7), 16);
  const luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue;
  return luminance < 70 ? "#f4faf7" : color;
}

export function PointsTrendChart({ clubs }: PointsTrendChartProps) {
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;
  const highestPoints = Math.max(
    90,
    ...clubs.flatMap((club) => club.points_by_matchweek),
  );
  const yMax = Math.ceil(highestPoints / 10) * 10;
  const yTicks = [0, 0.25, 0.5, 0.75, 1].map((value) =>
    Math.round(yMax * value),
  );
  const xTicks = [1, 10, 20, 30, 38];
  const xFor = (index: number) =>
    padding.left + (index / 37) * plotWidth;
  const yFor = (points: number) =>
    padding.top + plotHeight - (points / yMax) * plotHeight;

  return (
    <div className="form-trend-chart">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label={`${clubs.map((club) => club.club.short_name).join("与")}的38轮累计积分走势`}
      >
        {yTicks.map((tick) => {
          const y = yFor(tick);
          return (
            <g key={tick}>
              <line
                className="form-chart-grid"
                x1={padding.left}
                x2={width - padding.right}
                y1={y}
                y2={y}
              />
              <text className="form-chart-label" x={padding.left - 12} y={y + 4}>
                {tick}
              </text>
            </g>
          );
        })}
        {xTicks.map((tick) => (
          <text
            className="form-chart-label"
            key={tick}
            x={xFor(tick - 1)}
            y={height - 14}
            textAnchor="middle"
          >
            MW {tick}
          </text>
        ))}

        {clubs.map((club) => {
          const color = readableColor(club.club.primary_color);
          const points = club.points_by_matchweek
            .map((value, index) => `${xFor(index)},${yFor(value)}`)
            .join(" ");
          const finalPoints = club.points_by_matchweek.at(-1) ?? 0;
          return (
            <g key={club.club.slug}>
              <polyline
                className="form-chart-line"
                points={points}
                stroke={color}
              />
              <circle
                cx={xFor(37)}
                cy={yFor(finalPoints)}
                fill={color}
                r="5"
              />
            </g>
          );
        })}
      </svg>
      <div className="form-chart-legend" aria-hidden="true">
        {clubs.map((club) => (
          <span key={club.club.slug}>
            <i style={{ background: readableColor(club.club.primary_color) }} />
            {club.club.short_name} · {club.overall.points} 分
          </span>
        ))}
      </div>
    </div>
  );
}
