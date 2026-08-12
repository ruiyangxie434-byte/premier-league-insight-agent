"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import type { CSSProperties } from "react";

import { PlayerRadar } from "../../../components/players/player-radar";
import { SiteHeader } from "../../../components/system/site-header";
import { getPlayer, getSimilarPlayers } from "../../../services/api";
import type {
  PlayerLabItem,
  PlayerPer90Metrics,
  PlayerPosition,
  PlayerSimilarityData,
} from "../../../types/api";

type DetailState = "loading" | "success" | "error";
type SimilarityState = "loading" | "success" | "error";
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

function formatBirthDate(value: string | null, birthYear: number | null) {
  if (!value) {
    return birthYear ? `${birthYear} 年` : "未知";
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
  const [similarityState, setSimilarityState] =
    useState<SimilarityState>("loading");
  const [similarity, setSimilarity] =
    useState<PlayerSimilarityData | null>(null);
  const [similarityMinimumMinutes, setSimilarityMinimumMinutes] =
    useState(450);
  const [similarityRequestId, setSimilarityRequestId] = useState(0);

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

  useEffect(() => {
    const controller = new AbortController();

    async function loadSimilarity() {
      setSimilarityState("loading");
      try {
        const response = await getSimilarPlayers(
          params.slug,
          {
            season: "2024-25",
            minimumMinutes: similarityMinimumMinutes,
            limit: 5,
          },
          controller.signal,
        );
        if (!response.data) {
          throw new Error("相似球员数据为空");
        }
        setSimilarity(response.data);
        setSimilarityState("success");
      } catch {
        if (!controller.signal.aborted) {
          setSimilarityState("error");
        }
      }
    }

    void loadSimilarity();
    return () => controller.abort();
  }, [params.slug, similarityMinimumMinutes, similarityRequestId]);

  return (
    <main>
      <div className="page-shell player-detail-shell">
        <SiteHeader />

        <Link className="club-back-link" href="/players">
          <span aria-hidden="true">←</span>
          返回球员数据中心
        </Link>

        {state === "loading" && (
          <div className="player-lab-state" aria-live="polite">
            <span className="loading-ring" aria-hidden="true" />
            <div>
              <strong>正在读取球员赛季档案</strong>
              <p>获取累计数据、每90指标和位置百分位。</p>
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
                  <dt>{player.date_of_birth ? "出生日期" : "出生年份"}</dt>
                  <dd>{formatBirthDate(player.date_of_birth, player.birth_year)}</dd>
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
                  <small>赛季 xG</small>
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
                      {player.percentiles.scope === "position_pool"
                        ? `同位置 ${player.percentiles.peer_count} 条合格记录`
                        : `全部 ${player.percentiles.peer_count} 条合格记录`}
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

              <section
                className="similarity-scout"
                aria-labelledby="similarity-scout-title"
              >
                <div className="similarity-scout-heading">
                  <div>
                    <p className="eyebrow">SIMILARITY SCOUT · EXPLAINABLE MATCHING</p>
                    <h2 id="similarity-scout-title">同位置相似球员</h2>
                    <p>
                      用同位置百分位画像寻找风格接近的赛季记录，同时保留最接近指标与最大差异，避免把相似分当成绝对能力。
                    </p>
                  </div>
                  <label>
                    <span>候选分钟门槛</span>
                    <select
                      onChange={(event) =>
                        setSimilarityMinimumMinutes(Number(event.target.value))
                      }
                      value={similarityMinimumMinutes}
                    >
                      <option value={450}>450+ 分钟</option>
                      <option value={1800}>1,800+ 分钟</option>
                      <option value={2700}>2,700+ 分钟</option>
                    </select>
                  </label>
                </div>

                {similarityState === "loading" && (
                  <div className="similarity-state" aria-live="polite">
                    <span className="loading-ring" aria-hidden="true" />
                    <div>
                      <strong>正在匹配同位置画像</strong>
                      <p>计算七项百分位差异与位置权重。</p>
                    </div>
                  </div>
                )}

                {similarityState === "error" && (
                  <div className="similarity-state similarity-state-error" role="alert">
                    <div>
                      <strong>暂时无法读取相似球员</strong>
                      <p>球员资料仍可使用，可以单独重新加载该模块。</p>
                    </div>
                    <button
                      className="secondary-button"
                      onClick={() =>
                        setSimilarityRequestId((value) => value + 1)
                      }
                      type="button"
                    >
                      重新匹配
                    </button>
                  </div>
                )}

                {similarityState === "success" && similarity && (
                  <>
                    {!similarity.is_supported && (
                      <div className="similarity-unavailable">
                        <span>DATA BOUNDARY</span>
                        <strong>当前不生成相似度结果</strong>
                        <p>{similarity.unavailable_reason}</p>
                      </div>
                    )}

                    {similarity.is_supported && (
                      <>
                        <div className="similarity-model-summary">
                          <div>
                            <span>CANDIDATE POOL</span>
                            <strong>{similarity.candidate_total}</strong>
                            <small>
                              条 {positionLabels[similarity.position]}记录
                            </small>
                          </div>
                          <div className="similarity-weight-list">
                            {similarity.metric_weights.map((metric) => (
                              <span key={metric.key}>
                                {metric.label}
                                <b>{Math.round(metric.weight * 100)}%</b>
                              </span>
                            ))}
                          </div>
                        </div>

                        <ol className="similarity-card-grid">
                          {similarity.items.map((candidate, index) => (
                            <li key={candidate.player.slug}>
                              <article
                                className="similarity-card"
                                style={
                                  {
                                    "--candidate-color":
                                      candidate.player.club.primary_color,
                                    "--similarity-score":
                                      `${candidate.similarity_score}%`,
                                  } as CSSProperties
                                }
                              >
                                <div className="similarity-card-topline">
                                  <span>#{index + 1} MATCH</span>
                                  <div
                                    aria-label={`相似度 ${candidate.similarity_score} 分`}
                                    aria-valuemax={100}
                                    aria-valuemin={0}
                                    aria-valuenow={candidate.similarity_score}
                                    className="similarity-score"
                                    role="progressbar"
                                  >
                                    <strong>{candidate.similarity_score}</strong>
                                    <small>/100</small>
                                  </div>
                                </div>

                                <Link
                                  className="similarity-player-identity"
                                  href={`/players/${candidate.player.slug}`}
                                >
                                  <span>{initials(candidate.player.full_name)}</span>
                                  <div>
                                    <h3>{candidate.player.full_name}</h3>
                                    <p>
                                      {candidate.player.club.short_name} · {candidate.player.totals.minutes.toLocaleString("en-US")} 分钟
                                    </p>
                                  </div>
                                </Link>

                                <div className="similarity-closest-metrics">
                                  <span>最接近</span>
                                  {candidate.closest_metrics.map((metric) => (
                                    <b key={metric}>{metric}</b>
                                  ))}
                                </div>

                                <dl className="similarity-difference">
                                  <div>
                                    <dt>最大画像差异 · {candidate.key_difference.label}</dt>
                                    <dd>
                                      <span>
                                        {player.full_name} P{candidate.key_difference.target_percentile}
                                      </span>
                                      <span>
                                        {candidate.player.full_name} P{candidate.key_difference.candidate_percentile}
                                      </span>
                                    </dd>
                                  </div>
                                  <strong>Δ {candidate.key_difference.gap}</strong>
                                </dl>

                                <div className="similarity-card-actions">
                                  <Link href={`/players/${candidate.player.slug}`}>
                                    查看资料
                                  </Link>
                                  <Link
                                    href={`/players?compare=${encodeURIComponent(player.slug)},${encodeURIComponent(candidate.player.slug)}#player-radar`}
                                  >
                                    立即对比 →
                                  </Link>
                                </div>
                              </article>
                            </li>
                          ))}
                        </ol>
                      </>
                    )}

                    <p className="similarity-method-notice">
                      <span aria-hidden="true">i</span>
                      {similarity.method_notice}
                    </p>
                  </>
                )}
              </section>

              <div className="player-detail-footer">
                <p>
                  当前资料来自 Kaggle v1 的 2024-25 历史快照。默认百分位只描述达到 450 分钟的固定球员—球队记录池，不代表官方实时排名。
                </p>
                <div>
                  <Link className="secondary-button" href={`/clubs/${player.club.slug}`}>
                    查看球队资料
                  </Link>
                  <Link
                    className="primary-button"
                    href={`/players?compare=${encodeURIComponent(player.slug)}#player-radar`}
                  >
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
