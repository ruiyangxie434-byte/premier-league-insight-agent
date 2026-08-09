"use client";

import Image from "next/image";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import type { CSSProperties } from "react";

import { ShotMap } from "../../../components/matches/shot-map";
import { getMatch } from "../../../services/api";
import type { MatchDetailData, MatchShotData } from "../../../types/api";

type PageState = "loading" | "success" | "error";

const outcomeLabels: Record<string, string> = {
  Goal: "进球",
  Saved: "扑救",
  Blocked: "封堵",
  "Off T": "偏出",
  "Wayward": "偏出",
  Post: "中柱",
  "Saved to Post": "扑救后中柱",
};

function formatDate(value: string | null) {
  if (!value) {
    return "日期待确认";
  }
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(new Date(value));
}

function formatMinute(shot: MatchShotData) {
  return `${shot.minute + 1}′`;
}

function finishingDelta(goals: number, xg: number) {
  const value = goals - xg;
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}`;
}

export default function MatchDetailPage() {
  const params = useParams<{ sourceMatchId: string }>();
  const [state, setState] = useState<PageState>("loading");
  const [data, setData] = useState<MatchDetailData | null>(null);
  const [teamFilter, setTeamFilter] = useState("all");
  const [goalsOnly, setGoalsOnly] = useState(false);
  const [selectedShotId, setSelectedShotId] = useState<string | null>(null);
  const [requestId, setRequestId] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    async function loadMatch() {
      setState("loading");
      try {
        const response = await getMatch(
          params.sourceMatchId,
          controller.signal,
        );
        if (!response.data) {
          throw new Error("比赛详情为空");
        }
        setData(response.data);
        const highestValueShot = [...response.data.shots].sort(
          (left, right) => right.xg - left.xg,
        )[0];
        setSelectedShotId(highestValueShot?.source_event_id ?? null);
        setState("success");
      } catch {
        if (!controller.signal.aborted) {
          setState("error");
        }
      }
    }

    void loadMatch();
    return () => controller.abort();
  }, [params.sourceMatchId, requestId]);

  const visibleShots = useMemo(() => {
    if (!data) {
      return [];
    }
    return data.shots.filter(
      (shot) =>
        (teamFilter === "all" || shot.team_slug === teamFilter) &&
        (!goalsOnly || shot.is_goal),
    );
  }, [data, goalsOnly, teamFilter]);

  const selectedShot = useMemo(() => {
    return (
      visibleShots.find((shot) => shot.source_event_id === selectedShotId) ??
      visibleShots[0] ??
      null
    );
  }, [selectedShotId, visibleShots]);

  const goalTimeline = useMemo(() => {
    if (!data) {
      return [];
    }
    let homeScore = 0;
    let awayScore = 0;
    return data.shots
      .filter((shot) => shot.is_goal)
      .map((shot) => {
        if (shot.team_slug === data.home_team.slug) {
          homeScore += 1;
        } else {
          awayScore += 1;
        }
        return { shot, score: `${homeScore}–${awayScore}` };
      });
  }, [data]);

  const highestValueShot = useMemo(() => {
    if (!data) {
      return null;
    }
    return [...data.shots].sort((left, right) => right.xg - left.xg)[0] ?? null;
  }, [data]);

  return (
    <main>
      <div className="page-shell match-detail-shell">
        <header className="site-header">
          <Link className="brand" href="/" aria-label="英超智析 Agent 首页">
            <span className="brand-mark" aria-hidden="true">AI</span>
            <span>
              <strong>英超智析 Agent</strong>
              <small>Premier League Insight Agent</small>
            </span>
          </Link>
          <span className="phase-badge">v0.10.0 · Season Form Lab</span>
        </header>

        <Link className="club-back-link" href="/matches">
          <span aria-hidden="true">←</span>
          返回比赛中心
        </Link>

        {state === "loading" && (
          <div className="match-page-state" aria-live="polite">
            <span className="loading-ring" aria-hidden="true" />
            <div>
              <strong>正在重建比赛事件</strong>
              <p>聚合射门坐标、xG 与进球时间线。</p>
            </div>
          </div>
        )}

        {state === "error" && (
          <div className="match-page-state match-page-error" role="alert">
            <div>
              <span>MATCH SNAPSHOT OFFLINE</span>
              <strong>暂时无法打开比赛分析</strong>
              <p>请确认后端仍在运行，或返回比赛中心。</p>
            </div>
            <button
              className="secondary-button"
              type="button"
              onClick={() => setRequestId((value) => value + 1)}
            >
              重新读取
            </button>
          </div>
        )}

        {state === "success" && data && (
          <div
            className="match-detail-content"
            style={
              {
                "--home-color": data.home_team.primary_color,
                "--away-color": data.away_team.primary_color,
              } as CSSProperties
            }
          >
            <section className="match-score-hero" aria-labelledby="match-score-title">
              <div className="match-score-meta">
                <p className="eyebrow">{data.competition} · {data.season}</p>
                <span>{formatDate(data.kickoff_at)} · 第 {data.matchweek} 轮</span>
              </div>

              <div className="match-scoreboard" id="match-score-title">
                <Link href={`/clubs/${data.home_team.slug}`}>
                  <i className="match-team-mark home" aria-hidden="true" />
                  <strong>{data.home_team.short_name}</strong>
                  <small>主队</small>
                </Link>
                <div>
                  <span>{data.home_team.score}</span>
                  <b>:</b>
                  <span>{data.away_team.score}</span>
                </div>
                <Link href={`/clubs/${data.away_team.slug}`}>
                  <i className="match-team-mark away" aria-hidden="true" />
                  <strong>{data.away_team.short_name}</strong>
                  <small>客队</small>
                </Link>
              </div>

              <div className="match-score-venue">
                <span>{data.venue}</span>
                <span>StatsBomb Match ID · {data.source_match_id}</span>
              </div>
            </section>

            <section className="match-metric-grid" aria-label="比赛核心数据">
              <article>
                <span>SHOTS</span>
                <strong>{data.home_team.shots}<i>–</i>{data.away_team.shots}</strong>
                <small>双方共 {data.shot_count} 次</small>
              </article>
              <article>
                <span>EXPECTED GOALS</span>
                <strong>{data.home_team.total_xg.toFixed(2)}<i>–</i>{data.away_team.total_xg.toFixed(2)}</strong>
                <small>机会质量总和</small>
              </article>
              <article>
                <span>FINISHING Δ</span>
                <strong>{finishingDelta(data.home_team.goals, data.home_team.total_xg)}<i>–</i>{finishingDelta(data.away_team.goals, data.away_team.total_xg)}</strong>
                <small>进球减去 xG</small>
              </article>
              <article>
                <span>TOP CHANCE</span>
                <strong>{highestValueShot?.xg.toFixed(3) ?? "—"}</strong>
                <small>{highestValueShot?.player_name ?? "未知球员"}</small>
              </article>
            </section>

            <section className="shot-explorer-section" aria-labelledby="shot-explorer-title">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">SHOT EXPLORER</p>
                  <h2 id="shot-explorer-title">28 次射门，放回球场</h2>
                </div>
                <p>筛选球队或只看进球；点击圆点，查看球员、时间、结果与 xG。</p>
              </div>

              <div className="shot-filter-bar" aria-label="射门筛选">
                <button
                  type="button"
                  data-active={teamFilter === "all"}
                  aria-pressed={teamFilter === "all"}
                  onClick={() => setTeamFilter("all")}
                >
                  全部 <span>{data.shot_count}</span>
                </button>
                {[data.home_team, data.away_team].map((team) => (
                  <button
                    type="button"
                    data-active={teamFilter === team.slug}
                    aria-pressed={teamFilter === team.slug}
                    key={team.slug}
                    onClick={() => setTeamFilter(team.slug)}
                  >
                    <i style={{ background: team.primary_color }} />
                    {team.short_name} <span>{team.shots}</span>
                  </button>
                ))}
                <button
                  type="button"
                  data-active={goalsOnly}
                  aria-pressed={goalsOnly}
                  onClick={() => setGoalsOnly((current) => !current)}
                >
                  只看进球 <span>{data.goal_count}</span>
                </button>
              </div>

              <div className="shot-explorer-grid">
                <ShotMap
                  shots={visibleShots}
                  selectedShotId={selectedShot?.source_event_id ?? null}
                  onSelect={(shot) => setSelectedShotId(shot.source_event_id)}
                />

                <aside className="shot-inspector" aria-live="polite">
                  {selectedShot ? (
                    <>
                      <div className="shot-inspector-heading">
                        <span style={{ color: selectedShot.team_color }}>
                          {selectedShot.team_name}
                        </span>
                        <strong>{formatMinute(selectedShot)}</strong>
                      </div>
                      <h3>{selectedShot.player_name ?? "未知球员"}</h3>
                      <p className="shot-outcome" data-goal={selectedShot.is_goal}>
                        {outcomeLabels[selectedShot.outcome] ?? selectedShot.outcome}
                      </p>
                      <dl>
                        <div><dt>xG</dt><dd>{selectedShot.xg.toFixed(3)}</dd></div>
                        <div><dt>部位</dt><dd>{selectedShot.body_part ?? "未知"}</dd></div>
                        <div><dt>类型</dt><dd>{selectedShot.shot_type ?? "未知"}</dd></div>
                        <div><dt>进攻</dt><dd>{selectedShot.play_pattern ?? "未知"}</dd></div>
                        <div><dt>坐标</dt><dd>{selectedShot.x.toFixed(1)}, {selectedShot.y.toFixed(1)}</dd></div>
                      </dl>
                      <small>坐标已归一化到 0–100，仅表示射门起点。</small>
                    </>
                  ) : (
                    <div className="shot-inspector-empty">
                      <strong>当前筛选没有射门</strong>
                      <p>关闭“只看进球”或切换球队。</p>
                    </div>
                  )}
                </aside>
              </div>
            </section>

            <section className="goal-timeline-section" aria-labelledby="goal-timeline-title">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">GOAL TIMELINE</p>
                  <h2 id="goal-timeline-title">比分如何来到 4–2</h2>
                </div>
                <p>事件分钟按来源时间向上取整显示，比分按进球顺序重建。</p>
              </div>
              <div className="goal-timeline">
                {goalTimeline.map(({ shot, score }) => (
                  <button
                    type="button"
                    key={shot.source_event_id}
                    style={{ "--event-color": shot.team_color } as CSSProperties}
                    onClick={() => {
                      setTeamFilter("all");
                      setGoalsOnly(false);
                      setSelectedShotId(shot.source_event_id);
                      document.getElementById("shot-explorer-title")?.scrollIntoView();
                    }}
                  >
                    <span>{formatMinute(shot)}</span>
                    <i aria-hidden="true" />
                    <strong>{shot.player_name}</strong>
                    <small>{shot.team_name}</small>
                    <b>{score}</b>
                  </button>
                ))}
              </div>
            </section>

            <section className="shot-ledger-section" aria-labelledby="shot-ledger-title">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">EVENT LEDGER</p>
                  <h2 id="shot-ledger-title">当前筛选事件</h2>
                </div>
                <p>{visibleShots.length} / {data.shot_count} 次射门</p>
              </div>
              <div className="shot-ledger" role="list">
                {visibleShots.map((shot) => (
                  <button
                    type="button"
                    role="listitem"
                    data-selected={shot.source_event_id === selectedShot?.source_event_id}
                    key={shot.source_event_id}
                    onClick={() => setSelectedShotId(shot.source_event_id)}
                  >
                    <span>{formatMinute(shot)}</span>
                    <i style={{ background: shot.team_color }} aria-hidden="true" />
                    <strong>{shot.player_name ?? "未知球员"}</strong>
                    <small>{outcomeLabels[shot.outcome] ?? shot.outcome}</small>
                    <b>{shot.xg.toFixed(3)} xG</b>
                  </button>
                ))}
              </div>
            </section>

            <aside className="match-method-card">
              <div>
                <span>METHOD & BOUNDARY</span>
                <h2>看得见依据，也看得见边界。</h2>
              </div>
              <div>
                <p>{data.coordinate_note}</p>
                <p>{data.interpretation_note}</p>
              </div>
              <div className="match-method-links">
                <Image
                  className="statsbomb-logo"
                  src="/statsbomb-open-data.png"
                  alt="StatsBomb"
                  width={150}
                  height={24}
                />
                <a href={data.source_url} target="_blank" rel="noreferrer">原始事件 JSON ↗</a>
                <a href={data.license_url} target="_blank" rel="noreferrer">开放数据许可 ↗</a>
                <small>
                  来源：{data.source_name} · 上游更新 {data.source_last_updated.slice(0, 10)}
                </small>
              </div>
            </aside>
          </div>
        )}
      </div>
    </main>
  );
}
