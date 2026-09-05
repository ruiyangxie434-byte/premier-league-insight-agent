"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import type { CSSProperties } from "react";

import { PositionTimelineChart } from "../../components/form/position-timeline-chart";
import { SiteHeader } from "../../components/system/site-header";
import { getSeasonTimeline } from "../../services/api";
import type {
  SeasonTimelineData,
  TimelineClubStory,
  TimelineTableRow,
  TimelineZone,
} from "../../types/api";

type PageState = "loading" | "success" | "error";

const defaultClubs = [
  "liverpool",
  "arsenal",
  "manchester-city",
  "nottingham-forest",
];

const zoneLabels: Record<TimelineZone, string> = {
  leader: "榜首",
  top_four: "前四",
  mid_table: "中游",
  relegation: "降级区",
};

function movementLabel(change: number) {
  if (change > 0) {
    return `↑ ${change}`;
  }
  if (change < 0) {
    return `↓ ${Math.abs(change)}`;
  }
  return "—";
}

function windowLabel(window: TimelineClubStory["best_five_match_window"]) {
  return `MW ${window.start_matchweek}–${window.end_matchweek}`;
}

function StoryCard({
  story,
  currentRow,
}: {
  story: TimelineClubStory;
  currentRow: TimelineTableRow;
}) {
  return (
    <section className="timeline-story" aria-labelledby="timeline-story-title">
      <header>
        <div>
          <p className="eyebrow">CLUB SEASON STORY</p>
          <h2 id="timeline-story-title">{story.club.name}</h2>
        </div>
        <span style={{ borderColor: story.club.primary_color }}>
          MW {currentRow.matchweek} · 第 {currentRow.position}
        </span>
      </header>
      <div className="timeline-story-grid">
        <article>
          <span>起点 → 终点</span>
          <strong>
            {story.round_one_position}<i>→</i>{story.final_position}
          </strong>
          <p>相对第 1 轮净变化 {story.finish_change > 0 ? "+" : ""}{story.finish_change} 位</p>
        </article>
        <article>
          <span>排名边界</span>
          <strong>{story.peak_position}<i>/</i>{story.lowest_position}</strong>
          <p>最高 / 最低；首次出现在 MW {story.peak_rounds[0]} / {story.lowest_rounds[0]}</p>
        </article>
        <article>
          <span>区间停留</span>
          <strong>{story.leader_rounds}<i>/</i>{story.top_four_rounds}</strong>
          <p>榜首 / 前四轮数 · 降级区 {story.relegation_rounds} 轮</p>
        </article>
        <article>
          <span>最佳五轮</span>
          <strong>{story.best_five_match_window.points}<small> / 15</small></strong>
          <p>{windowLabel(story.best_five_match_window)} · {story.best_five_match_window.points_per_game.toFixed(2)} PPG</p>
        </article>
        <article>
          <span>最低五轮</span>
          <strong>{story.worst_five_match_window.points}<small> / 15</small></strong>
          <p>{windowLabel(story.worst_five_match_window)} · {story.worst_five_match_window.points_per_game.toFixed(2)} PPG</p>
        </article>
        <article>
          <span>最大单轮波动</span>
          <strong>
            +{story.biggest_rise?.places ?? 0}<i>/</i>-{story.biggest_drop?.places ?? 0}
          </strong>
          <p>上升 MW {story.biggest_rise?.matchweek ?? "—"} · 下滑 MW {story.biggest_drop?.matchweek ?? "—"}</p>
        </article>
      </div>
    </section>
  );
}

export default function SeasonTimelinePage() {
  const [state, setState] = useState<PageState>("loading");
  const [data, setData] = useState<SeasonTimelineData | null>(null);
  const [selectedMatchweek, setSelectedMatchweek] = useState(38);
  const [selectedSlugs, setSelectedSlugs] = useState(defaultClubs);
  const [activeSlug, setActiveSlug] = useState("liverpool");
  const [isPlaying, setIsPlaying] = useState(false);
  const [requestId, setRequestId] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    async function loadTimeline() {
      setState("loading");
      try {
        const response = await getSeasonTimeline("2024-25", controller.signal);
        if (!response.data) {
          throw new Error("赛季时间轴数据为空");
        }
        const query = new URLSearchParams(window.location.search);
        const queryClub = query.get("club");
        const queryMatchweek = Number(query.get("matchweek"));
        const validClub = response.data.club_stories.some(
          (item) => item.club.slug === queryClub,
        );
        if (validClub && queryClub) {
          setActiveSlug(queryClub);
          setSelectedSlugs((current) =>
            current.includes(queryClub)
              ? current
              : [queryClub, ...current.slice(0, 3)],
          );
        }
        if (Number.isInteger(queryMatchweek) && queryMatchweek >= 1 && queryMatchweek <= 38) {
          setSelectedMatchweek(queryMatchweek);
        }
        setData(response.data);
        setState("success");
      } catch {
        if (!controller.signal.aborted) {
          setState("error");
        }
      }
    }
    void loadTimeline();
    return () => controller.abort();
  }, [requestId]);

  useEffect(() => {
    if (!isPlaying) {
      return;
    }
    const timer = window.setInterval(() => {
      setSelectedMatchweek((current) => (current >= 38 ? 1 : current + 1));
    }, 650);
    return () => window.clearInterval(timer);
  }, [isPlaying]);

  const currentRound = data?.rounds[selectedMatchweek - 1] ?? null;
  const activeStory = useMemo(
    () => data?.club_stories.find((item) => item.club.slug === activeSlug) ?? null,
    [activeSlug, data],
  );
  const activeRow = currentRound?.rows.find((row) => row.club.slug === activeSlug) ?? null;
  const clubsLed = useMemo(
    () => new Set(data?.leader_changes.map((item) => item.leader.slug) ?? []).size,
    [data],
  );
  const biggestMover = useMemo(() => {
    if (!currentRound) {
      return null;
    }
    return maxBy(currentRound.rows, (row) => Math.abs(row.position_change));
  }, [currentRound]);

  function focusClub(slug: string) {
    setActiveSlug(slug);
    setSelectedSlugs((current) => {
      if (current.includes(slug)) {
        return current;
      }
      return current.length < 4
        ? [...current, slug]
        : [...current.slice(0, 3), slug];
    });
  }

  function toggleTrajectory(slug: string) {
    setSelectedSlugs((current) => {
      if (current.includes(slug)) {
        return current.length === 1
          ? current
          : current.filter((item) => item !== slug);
      }
      return current.length >= 4 ? current : [...current, slug];
    });
    setActiveSlug(slug);
  }

  return (
    <main className="timeline-page">
      <div className="page-shell timeline-shell">
        <SiteHeader />

        <div className="timeline-toplinks">
          <Link className="club-back-link" href="/">← 返回地图首页</Link>
          <Link className="secondary-button" href="/form">赛季状态实验室 →</Link>
        </div>

        <section className="timeline-hero" aria-labelledby="timeline-title">
          <div>
            <p className="eyebrow">SEASON TIMELINE LAB · 760 TABLE ROWS</p>
            <h1 id="timeline-title">
              最终排名之前，
              <span>每一轮都在移动。</span>
            </h1>
            <p>
              用 380 场完整比分重建 38 轮积分榜，拖动轮次查看升降、五轮状态和榜首更替，再沿单队轨迹找到赛季峰值与低谷。
            </p>
          </div>
          <div className="timeline-hero-orbit" aria-hidden="true">
            <span>01</span><span>10</span><span>20</span><span>30</span><span>38</span>
            <strong>MW</strong>
          </div>
        </section>

        {state === "loading" && (
          <div className="match-page-state" aria-live="polite">
            <span className="loading-ring" aria-hidden="true" />
            <div><strong>正在重建 38 轮积分榜</strong><p>计算 20 支球队的排名、升降与滚动状态。</p></div>
          </div>
        )}

        {state === "error" && (
          <div className="match-page-state match-page-error" role="alert">
            <div><span>TIMELINE OFFLINE</span><strong>暂时无法读取赛季时间轴</strong><p>请确认后端仍在运行，再重新加载。</p></div>
            <button className="secondary-button" type="button" onClick={() => setRequestId((value) => value + 1)}>重新读取</button>
          </div>
        )}

        {state === "success" && data && currentRound && activeStory && activeRow && (
          <>
            <section className="timeline-kpis" aria-label="时间轴摘要">
              <article><span>ROUNDS</span><strong>{data.total_matchweeks}</strong><small>{data.match_count} 场赛果</small></article>
              <article><span>LEAD CHANGES</span><strong>{Math.max(0, data.leader_changes.length - 1)}</strong><small>{clubsLed} 队曾领跑</small></article>
              <article><span>CURRENT LEADER</span><strong>{currentRound.leader.short_name}</strong><small>第 {selectedMatchweek} 轮快照</small></article>
              <article><span>BIGGEST MOVE</span><strong>{biggestMover ? movementLabel(biggestMover.position_change) : "—"}</strong><small>{biggestMover?.club.short_name ?? "无变化"}</small></article>
            </section>

            <section className="timeline-console" aria-labelledby="timeline-console-title">
              <header>
                <div><p className="eyebrow">MATCHWEEK CONTROL</p><h2 id="timeline-console-title">第 {selectedMatchweek} 轮积分榜</h2></div>
                <div className="timeline-playback">
                  <button type="button" onClick={() => setSelectedMatchweek((value) => Math.max(1, value - 1))}>←</button>
                  <button type="button" data-playing={isPlaying} onClick={() => setIsPlaying((value) => !value)}>{isPlaying ? "暂停" : "播放"}</button>
                  <button type="button" onClick={() => setSelectedMatchweek((value) => Math.min(38, value + 1))}>→</button>
                </div>
              </header>
              <div className="timeline-range-row">
                <span>MW 1</span>
                <input
                  aria-label="选择比赛轮次"
                  type="range"
                  min="1"
                  max="38"
                  value={selectedMatchweek}
                  onChange={(event) => {
                    setIsPlaying(false);
                    setSelectedMatchweek(Number(event.target.value));
                  }}
                  style={{ "--timeline-progress": `${((selectedMatchweek - 1) / 37) * 100}%` } as CSSProperties}
                />
                <span>MW 38</span>
              </div>

              <div className="timeline-club-picker" aria-label="排名轨迹球队选择">
                {data.club_stories.map((story) => {
                  const selected = selectedSlugs.includes(story.club.slug);
                  return (
                    <button
                      type="button"
                      data-selected={selected}
                      data-active={activeSlug === story.club.slug}
                      onClick={() => toggleTrajectory(story.club.slug)}
                      key={story.club.slug}
                      title={selected ? "从轨迹图移除" : "加入轨迹图（最多四队）"}
                    >
                      <i style={{ background: story.club.primary_color }} />
                      {story.club.short_name}
                    </button>
                  );
                })}
              </div>
              <p className="timeline-picker-note">绿色描边为故事焦点；实心按钮已加入轨迹图，最多同时显示四队。</p>
            </section>

            <section className="timeline-trajectory" aria-labelledby="trajectory-title">
              <div className="section-heading">
                <div><p className="eyebrow">POSITION TRAJECTORY</p><h2 id="trajectory-title">38 轮排名轨迹</h2></div>
                <p>第 1 名位于图表上方；绿色区域标记前四，红色区域标记第 18–20 名。</p>
              </div>
              <PositionTimelineChart rounds={data.rounds} selectedSlugs={selectedSlugs} currentMatchweek={selectedMatchweek} />
            </section>

            <div className="timeline-main-grid">
              <section className="timeline-table-card" aria-labelledby="round-table-title">
                <header><div><p className="eyebrow">ROUND TABLE</p><h2 id="round-table-title">MW {selectedMatchweek} 完整排名</h2></div><span>{currentRound.leader.short_name} 领跑</span></header>
                <div className="timeline-table-scroll">
                  <table>
                    <thead><tr><th>#</th><th>移动</th><th>球队</th><th>赛</th><th>胜-平-负</th><th>净胜</th><th>近五轮</th><th>分</th></tr></thead>
                    <tbody>
                      {currentRound.rows.map((row) => (
                        <tr key={row.club.slug} data-zone={row.zone} data-active={row.club.slug === activeSlug}>
                          <td><strong>{row.position}</strong></td>
                          <td><span className="timeline-movement" data-change={Math.sign(row.position_change)}>{movementLabel(row.position_change)}</span></td>
                          <td><button type="button" onClick={() => focusClub(row.club.slug)}><i style={{ background: row.club.primary_color }} /><span>{row.club.name}</span><small>{zoneLabels[row.zone]}</small></button></td>
                          <td>{row.played}</td><td>{row.won}-{row.drawn}-{row.lost}</td><td>{row.goal_difference > 0 ? "+" : ""}{row.goal_difference}</td><td>{row.rolling_points}<small> / {Math.min(5, row.played) * 3}</small></td><td><strong>{row.points}</strong></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>

              <aside className="timeline-leader-log" aria-labelledby="leader-log-title">
                <header><p className="eyebrow">LEADER LOG</p><h2 id="leader-log-title">榜首更替</h2><span>{data.leader_changes.length - 1} 次变化</span></header>
                <ol>
                  {data.leader_changes.map((change) => (
                    <li key={`${change.matchweek}-${change.leader.slug}`} data-future={change.matchweek > selectedMatchweek}>
                      <span>MW {change.matchweek}</span>
                      <i style={{ background: change.leader.primary_color }} />
                      <div><strong>{change.leader.short_name}</strong><small>{change.previous_leader ? `取代 ${change.previous_leader.short_name}` : "初始轮次榜首"}</small></div>
                    </li>
                  ))}
                </ol>
              </aside>
            </div>

            <StoryCard story={activeStory} currentRow={activeRow} />

            <aside className="timeline-boundary">
              <div><span>METHOD</span><strong>轮次重建，不是实时回放</strong></div>
              <p>{data.method_notice}</p>
              <p>{data.sample_notice}</p>
              <a href={data.source_url} target="_blank" rel="noreferrer">{data.source_name} · {data.license_name} ↗</a>
            </aside>
          </>
        )}
      </div>
    </main>
  );
}

function maxBy<T>(items: T[], score: (item: T) => number): T | null {
  return items.reduce<T | null>(
    (best, item) => best === null || score(item) > score(best) ? item : best,
    null,
  );
}
