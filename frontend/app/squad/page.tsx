"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { SiteHeader } from "../../components/system/site-header";
import { getClubs, getSquadLens } from "../../services/api";
import type {
  ClubSummary,
  SquadLensData,
  SquadPosition,
} from "../../types/api";

const positionCodes: Record<SquadPosition, string> = {
  GK: "01",
  DEF: "02",
  MID: "03",
  FWD: "04",
};

const minuteOptions = [
  { value: 0, label: "全部记录" },
  { value: 450, label: "450+ 分钟" },
  { value: 900, label: "900+ 分钟" },
  { value: 1800, label: "1800+ 分钟" },
];

function formatNumber(value: number) {
  return new Intl.NumberFormat("zh-CN").format(value);
}

export default function SquadPage() {
  const [clubs, setClubs] = useState<ClubSummary[]>([]);
  const [clubSlug, setClubSlug] = useState("liverpool");
  const [minimumMinutes, setMinimumMinutes] = useState(450);
  const [data, setData] = useState<SquadLensData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    getClubs(controller.signal)
      .then((response) => {
        const items = response.data?.items ?? [];
        setClubs(items);
        const queryClub = new URLSearchParams(window.location.search).get("club");
        if (queryClub && items.some((club) => club.slug === queryClub)) {
          setLoading(true);
          setError(false);
          setClubSlug(queryClub);
        }
      })
      .catch(() => undefined);
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    getSquadLens(clubSlug, minimumMinutes, "2024-25", controller.signal)
      .then((response) => {
        if (!response.data) throw new Error("阵容数据为空");
        setData(response.data);
      })
      .catch(() => {
        if (!controller.signal.aborted) setError(true);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [clubSlug, minimumMinutes]);

  function chooseClub(next: string) {
    setLoading(true);
    setError(false);
    setClubSlug(next);
    window.history.replaceState(null, "", `/squad?club=${encodeURIComponent(next)}`);
  }

  function chooseMinimumMinutes(next: number) {
    setLoading(true);
    setError(false);
    setMinimumMinutes(next);
  }

  return (
    <main className="squad-page">
      <div className="page-shell squad-shell">
        <SiteHeader />
        <Link className="club-back-link" href="/players">
          <span aria-hidden="true">←</span>返回球员实验室
        </Link>

        <section className="squad-hero">
          <div>
            <p className="eyebrow">SQUAD LENS · HISTORICAL SNAPSHOT</p>
            <h1>看清阵容，<span>不猜阵型。</span></h1>
            <p>把 2024–25 球员—俱乐部快照压缩成位置分钟、队内领跑者与核心负荷。所有结论均可追溯到固定数据记录。</p>
          </div>
          <div className="squad-hero-proof">
            <span>DATA CONTRACT</span>
            <strong>XI</strong>
            <small>MINUTES · ROLES · LOAD</small>
          </div>
        </section>

        <section className="squad-controls" aria-label="阵容筛选">
          <label>
            <span>选择球队</span>
            <select value={clubSlug} onChange={(event) => chooseClub(event.target.value)}>
              {clubs.map((club) => <option key={club.slug} value={club.slug}>{club.name}</option>)}
            </select>
          </label>
          <label>
            <span>分析分钟门槛</span>
            <select value={minimumMinutes} onChange={(event) => chooseMinimumMinutes(Number(event.target.value))}>
              {minuteOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
          </label>
          <div><span>当前状态</span><strong>{loading ? "正在重算" : "固定快照"}</strong></div>
        </section>

        {error && <div className="match-page-state match-page-error"><div><strong>阵容数据读取失败</strong><p>请确认后端正在运行，或降低分钟门槛后重试。</p></div></div>}

        {data && <div className={loading ? "squad-content is-refreshing" : "squad-content"}>
          <section className="squad-club-heading" style={{ borderColor: data.club.primary_color }}>
            <div><span>2024–25 · {data.club.short_name}</span><h2>{data.club.name}</h2></div>
            <p>{data.qualified_total} 条合格记录 / {data.record_total} 条阵容记录<small>排除 {data.excluded_total} 条低于当前分钟门槛的记录</small></p>
          </section>

          <section className="squad-kpis" aria-label="阵容概览">
            <article><span>分析池</span><strong>{data.qualified_total}<small> / {data.record_total}</small></strong><p>合格 / 全部记录</p></article>
            <article><span>球员分钟</span><strong>{formatNumber(data.total_minutes)}</strong><p>当前门槛内合计</p></article>
            <article><span>进球 + 助攻</span><strong>{data.total_goals + data.total_assists}</strong><p>{data.total_goals} 球 · {data.total_assists} 助</p></article>
            <article><span>国籍覆盖</span><strong>{data.unique_nationalities}</strong><p>合格记录去重</p></article>
            <article><span>前五负荷</span><strong>{data.top_five_minutes_share.toFixed(1)}%</strong><p>分析池分钟占比</p></article>
          </section>

          <section className="squad-section">
            <div className="section-heading"><div><p className="eyebrow">POSITION BALANCE</p><h2>位置结构</h2></div><p>占比只按合格记录的出场分钟计算，不等于阵型或比赛站位。</p></div>
            <div className="squad-position-grid">
              {data.position_groups.map((group) => <article key={group.position}>
                <header><span>{positionCodes[group.position]}</span><strong>{group.position}</strong><small>{group.label}</small></header>
                <div className="squad-position-value"><strong>{group.minutes_share.toFixed(1)}%</strong><span>{formatNumber(group.minutes)} 分钟</span></div>
                <div className="squad-position-bar"><i style={{ width: `${group.minutes_share}%` }} /></div>
                <dl><div><dt>记录</dt><dd>{group.record_count}</dd></div><div><dt>进球</dt><dd>{group.goals}</dd></div><div><dt>助攻</dt><dd>{group.assists}</dd></div></dl>
              </article>)}
            </div>
          </section>

          <section className="squad-section">
            <div className="section-heading"><div><p className="eyebrow">ROLE LEADERS</p><h2>队内领跑者</h2></div><p>按原始赛季总量排序；同值时优先出场分钟更多的记录。</p></div>
            <div className="squad-leader-grid">
              {data.leaders.map((leader) => <article key={leader.metric}>
                <span>{leader.label}</span><strong>{formatNumber(leader.value)}<small>{leader.unit}</small></strong>
                <Link href={`/players/${leader.player.slug}`}>{leader.player.full_name}<small>{leader.player.position} · {leader.player.nationality}</small></Link>
              </article>)}
            </div>
          </section>

          <section className="squad-core">
            <div><p className="eyebrow">CORE LOAD</p><h2>出场核心记录</h2><p>按球员分钟从高到低展示前八名，用于观察赛季负荷集中度。</p></div>
            <ol>{data.core_players.map((player, index) => <li key={player.slug}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              <Link href={`/players/${player.slug}`}><strong>{player.full_name}</strong><small>{player.position} · {player.nationality}</small></Link>
              <div><strong>{formatNumber(player.minutes)}</strong><small>分钟 · {player.minutes_share.toFixed(1)}%</small></div>
              <div><strong>{player.goals + player.assists}</strong><small>进球 + 助攻</small></div>
            </li>)}</ol>
          </section>

          <section className="squad-method">
            <div><p className="eyebrow">GROUNDED SUMMARY</p><h2>机器汇总与边界</h2></div>
            <div><ul>{data.summary.map((item) => <li key={item}>{item}</li>)}</ul><p>{data.sample_notice}</p><p>{data.method_notice}</p></div>
            <footer><span>{data.source_name} · v{data.source_version}</span><a href={data.source_url} target="_blank" rel="noreferrer">查看原始数据源 →</a></footer>
          </section>
        </div>}
      </div>
    </main>
  );
}
