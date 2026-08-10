"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import type { CSSProperties } from "react";

import { PlayerRadar } from "../../../components/players/player-radar";
import { getPlayer } from "../../../services/api";
import type {
  PlayerLabItem,
  PlayerPer90Metrics,
  PlayerPosition,
} from "../../../types/api";

type DetailState = "loading" | "success" | "error";
type MetricKey = keyof PlayerPer90Metrics;

const positionLabels: Record<PlayerPosition, string> = {
  FWD: "前锋",
  MID: "中场",
  DEF: "后卫",
  GK: "门将",
};

const metrics: Array<{ key: MetricKey; label: string; hint: string }> = [
  { key: "goals_per90", label: "进球", hint: "GOALS / 90" },
  { key: "assists_per90", label: "助攻", hint: "ASSISTS / 90" },
  { key: "shots_per90", label: "射门", hint: "SHOTS / 90" },
  {
    key: "key_passes_per90",
    label: "关键传球",
    hint: "KEY PASSES / 90",
  },
  { key: "tackles_per90", label: "抢断", hint: "TACKLES / 90" },
  {
    key: "interceptions_per90",
    label: "拦截",
    hint: "INTERCEPTIONS / 90",
  },
  { key: "expected_goals_per90", label: "预期进球", hint: "xG / 90" },
];

function initials(name: string) {
  return name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 3)
    .toUpperCase();
}

function formatBirthDate(value: string | null) {
  if (!value) {
    return "未知";
  }
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "long",
    day: "numeric",
    timeZone: "UTC",
  }).format(new Date(`${value}T00:00:00Z`));
}

export default function PlayerDetailPage() {
  const params = useParams<{ slug: string }>();
  const [state, setState] = useState<DetailState>("loading");
  const [player, setPlayer] = useState<PlayerLabItem | null>(null);
  const [requestId, setRequestId] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    async function loadPlayer() {
      setState("loading");
      try {
        const response = await getPlayer(
          params.slug,
          "2024-25",
          controller.signal,
        );
        if (!response.data) {
          throw new Error("球员详情为空");
        }
        setPlayer(response.data);
        setState("success");
      } catch {
        if (!controller.signal.aborted) {
          setState("error");
        }
      }
    }

    void loadPlayer();
    return () => controller.abort();
  }, [params.slug, requestId]);

  return (
    <main>
      <div className="page-shell player-detail-shell">
        <header className="site-header">
          <Link className="brand" href="/" aria-label="英超智析 Agent 首页">
            <span className="brand-mark" aria-hidden="true">
              AI
            </span>
            <span>
              <strong>英超智析 Agent</strong>
              <small>Premier League Insight Agent</small>
            </span>
          </Link>
          <span className="phase-badge">v0.11.0 · League Copilot</span>
        </header>

        <Link className="club-back-link" href="/players">
          <span aria-hidden="true">←</span>
          返回球员数据中心
        </Link>

        {state === "loading" && (
          <div className="player-lab-state" aria-live="polite">
            <span className="loading-ring" aria-hidden="true" />
            <div>
              <strong>正在读取球员赛季档案</strong>
              <p>获取累计数据、每90指标和样例百分位。</p>
            </div>
          </div>
        )}

        {state === "error" && (
          <div className="player-lab-state player-lab-error" role="alert">
            <div>
              <strong>暂时无法打开球员资料</strong>
              <p>请确认后端仍在运行，或返回球员中心选择其他球员。</p>
            </div>
            <button
              className="secondary-button"
              onClick={() => setRequestId((value) => value + 1)}
              type="button"
            >
              重新读取
            </button>
          </div>
        )}

        {state === "success" && player && (
          <div
            className="player-detail-content"
            style={
              {
                "--player-club-color": player.club.primary_color,
              } as CSSProperties
            }
          >
            <section className="player-profile-hero">
              <div className="player-profile-mark" aria-hidden="true">
                <span>{player.shirt_number ?? "—"}</span>
                <strong>{initials(player.full_name)}</strong>
              </div>
              <div className="player-profile-copy">
                <p className="eyebrow">PLAYER PROFILE · {player.season}</p>
                <h1>{player.full_name}</h1>
                <p>
                  {player.club.name} · {positionLabels[player.position]} · {player.nationality}
                </p>
              </div>
              <dl className="player-profile-facts">
                <div>
                  <dt>出生日期</dt>
                  <dd>{formatBirthDate(player.date_of_birth)}</dd>
                </div>
                <div>
                  <dt>出场 / 首发</dt>
                  <dd>
                    {player.totals.appearances} / {player.totals.starts}
                  </dd>
                </div>
                <div>
                  <dt>赛季分钟</dt>
                  <dd>{player.totals.minutes.toLocaleString("en-US")}</dd>
                </div>
              </dl>
            </section>

            <section className="player-detail-overview">
              <div className="player-total-grid">
                <article>
                  <span>GOALS</span>
                  <strong>{player.totals.goals}</strong>
                  <small>赛季进球</small>
                </article>
                <article>
                  <span>ASSISTS</span>
                  <strong>{player.totals.assists}</strong>
                  <small>赛季助攻</small>
                </article>
                <article>
                  <span>SHOTS</span>
                  <strong>{player.totals.shots}</strong>
                  <small>射门次数</small>
                </article>
                <article>
                  <span>EXPECTED GOALS</span>
                  <strong>{player.totals.expected_goals?.toFixed(1) ?? "—"}</strong>
                  <small>赛季 xG 样例</small>
                </article>
              </div>

              <div className="player-detail-analysis">
                <article className="player-single-radar">
                  <div className="detail-panel-title">
                    <div>
                      <span>01</span>
                      <h2>能力结构</h2>
                    </div>
                    <small>
                      {player.percentiles.scope === "position_sample"
                        ? `同位置 ${player.percentiles.peer_count} 人样例`
                        : `全部 ${player.percentiles.peer_count} 人样例`}
                    </small>
                  </div>
                  <PlayerRadar players={[player]} />
                </article>

                <article className="player-metric-panel">
                  <div className="detail-panel-title">
                    <div>
                      <span>02</span>
                      <h2>每90分钟指标</h2>
                    </div>
                    <small>VALUE · PERCENTILE</small>
                  </div>
                  <div className="player-detail-metrics">
                    {metrics.map((metric) => {
                      const value = player.per90[metric.key];
                      const percentile =
                        player.percentiles.metrics[metric.key];
                      return (
                        <div key={metric.key}>
                          <div>
                            <span>{metric.label}</span>
                            <small>{metric.hint}</small>
                          </div>
                          <strong>{value.toFixed(2)}</strong>
                          <div className="detail-percentile-bar">
                            <i style={{ width: `${percentile}%` }} />
                          </div>
                          <b>P{percentile}</b>
                        </div>
                      );
                    })}
                  </div>
                </article>
              </div>

              <div className="player-detail-footer">
                <p>
                  当前资料来自项目演示样例，百分位只描述小型样例池内的相对位置，不代表官方实时球员排名。
                </p>
                <div>
                  <Link className="secondary-button" href={`/clubs/${player.club.slug}`}>
                    查看球队资料
                  </Link>
                  <Link className="primary-button" href="/players#player-radar">
                    加入双人对比
                  </Link>
                </div>
              </div>
            </section>
          </div>
        )}
      </div>
    </main>
  );
}
