import type { PlayerLabItem, PlayerMetricPercentiles } from "../../types/api";

type RadarMetricKey = keyof Pick<
  PlayerMetricPercentiles,
  | "goals_per90"
  | "assists_per90"
  | "shots_per90"
  | "key_passes_per90"
  | "tackles_per90"
  | "interceptions_per90"
>;

const axes: Array<{ key: RadarMetricKey; label: string }> = [
  { key: "goals_per90", label: "进球" },
  { key: "assists_per90", label: "助攻" },
  { key: "key_passes_per90", label: "关键传球" },
  { key: "interceptions_per90", label: "拦截" },
  { key: "tackles_per90", label: "抢断" },
  { key: "shots_per90", label: "射门" },
];

const centerX = 260;
const centerY = 205;
const chartRadius = 138;

function getPoint(index: number, radius: number) {
  const angle = -Math.PI / 2 + (index * Math.PI * 2) / axes.length;
  return {
    x: centerX + Math.cos(angle) * radius,
    y: centerY + Math.sin(angle) * radius,
  };
}

function getPolygonPoints(radius: number) {
  return axes
    .map((_, index) => {
      const point = getPoint(index, radius);
      return `${point.x.toFixed(1)},${point.y.toFixed(1)}`;
    })
    .join(" ");
}

function getPlayerPoints(player: PlayerLabItem) {
  return axes
    .map((axis, index) => {
      const percentile = player.percentiles.metrics[axis.key];
      const point = getPoint(index, (chartRadius * percentile) / 100);
      return `${point.x.toFixed(1)},${point.y.toFixed(1)}`;
    })
    .join(" ");
}

function getSeriesColors(players: PlayerLabItem[]) {
  if (
    players.length === 2 &&
    players[0].club.primary_color.toLowerCase() ===
      players[1].club.primary_color.toLowerCase()
  ) {
    return [players[0].club.primary_color, "#f4c95d"];
  }
  return players.map((player) => player.club.primary_color);
}

export function PlayerRadar({ players }: { players: PlayerLabItem[] }) {
  if (players.length === 0) {
    return (
      <div className="radar-empty">
        请选择一至两名球员，雷达图会在这里生成。
      </div>
    );
  }

  const colors = getSeriesColors(players);

  return (
    <div className="radar-visual">
      <svg
        aria-label={`${players.map((player) => player.full_name).join(" 与 ")}的每90分钟合格球员池百分位雷达图`}
        role="img"
        viewBox="0 0 520 430"
      >
        {[25, 50, 75, 100].map((level) => (
          <polygon
            className="radar-grid-ring"
            key={level}
            points={getPolygonPoints((chartRadius * level) / 100)}
          />
        ))}

        {axes.map((axis, index) => {
          const end = getPoint(index, chartRadius);
          const label = getPoint(index, chartRadius + 38);
          const anchor =
            Math.abs(label.x - centerX) < 10
              ? "middle"
              : label.x > centerX
                ? "start"
                : "end";
          return (
            <g key={axis.key}>
              <line
                className="radar-axis-line"
                x1={centerX}
                x2={end.x}
                y1={centerY}
                y2={end.y}
              />
              <text
                className="radar-axis-label"
                dominantBaseline="middle"
                textAnchor={anchor}
                x={label.x}
                y={label.y}
              >
                {axis.label}
              </text>
            </g>
          );
        })}

        {players.map((player, index) => (
          <g key={player.slug}>
            <polygon
              className="radar-series-area"
              fill={colors[index]}
              points={getPlayerPoints(player)}
              stroke={colors[index]}
            />
            {axes.map((axis, axisIndex) => {
              const percentile = player.percentiles.metrics[axis.key];
              const point = getPoint(
                axisIndex,
                (chartRadius * percentile) / 100,
              );
              return (
                <circle
                  className="radar-series-point"
                  cx={point.x}
                  cy={point.y}
                  fill={colors[index]}
                  key={axis.key}
                  r="4"
                >
                  <title>
                    {player.full_name} · {axis.label} P{percentile}
                  </title>
                </circle>
              );
            })}
          </g>
        ))}
      </svg>

      <div className="radar-legend" aria-label="雷达图图例">
        {players.map((player, index) => (
          <span key={player.slug}>
            <i style={{ background: colors[index] }} />
            {player.full_name}
          </span>
        ))}
      </div>
    </div>
  );
}
