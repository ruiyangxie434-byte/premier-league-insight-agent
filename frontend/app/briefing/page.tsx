"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { SiteHeader } from "../../components/system/site-header";
import { getClubBriefing, getClubs } from "../../services/api";
import type {
  ClubBriefingData,
  ClubSummary,
  FormResult,
} from "../../types/api";

const minuteOptions = [450, 900, 1800];
const preferenceKey = "pl-insight:briefing-club";
const resultLabels: Record<FormResult, string> = {
  W: "胜",
  D: "平",
  L: "负",
};

function formatNumber(value: number) {
  return new Intl.NumberFormat("zh-CN").format(value);
}

export default function BriefingPage() {
  const [clubs, setClubs] = useState<ClubSummary[]>([]);
  const [clubSlug, setClubSlug] = useState("liverpool");
  const [minimumMinutes, setMinimumMinutes] = useState(900);
  const [data, setData] = useState<ClubBriefingData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    getClubs(controller.signal)
      .then((response) => {
        const items = response.data?.items ?? [];
        setClubs(items);
        const queryClub = new URLSearchParams(window.location.search).get("club");
        const savedClub = window.localStorage.getItem(preferenceKey);
        const preferred = queryClub || savedClub;
        if (preferred && items.some((club) => club.slug === preferred)) {
          setLoading(true);
          setError(false);
          setClubSlug(preferred);
        }
      })
      .catch(() => undefined);
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    getClubBriefing(
      clubSlug,
      minimumMinutes,
      "2024-25",
      controller.signal,
    )
      .then((response) => {
        if (!response.data) throw new Error("球队情报简报为空");
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
    window.localStorage.setItem(preferenceKey, next);
    const search = new URLSearchParams({ club: next });
    window.history.replaceState(null, "", `/briefing?${search.toString()}`);
  }

  function chooseMinimumMinutes(next: number) {
    setLoading(true);
    setError(false);
    setMinimumMinutes(next);
  }

  return (
    <main className="briefing-page">
      <div className="page-shell briefing-shell">
        <div className="briefing-screen-only">
          <SiteHeader />
          <Link className="club-back-link" href="/">
            <span aria-hidden="true">←</span>返回项目首页
          </Link>

          <section className="briefing-hero">
            <div>
              <p className="eyebrow">CLUB BRIEFING ROOM · GROUNDED DOSSIER</p>
              <h1>一份简报，<span>串起全部证据。</span></h1>
              <p>
                把赛季终态、主客场、末五场、阵容负荷与三条位置候选信号
                组合成可核查、可打印的球队情报文件。
              </p>
            </div>
            <div className="briefing-hero-mark" aria-hidden="true">
              <span>INTELLIGENCE FILE</span>
              <strong>BRF</strong>
              <small>FORM · SQUAD · SIGNAL</small>
            </div>
          </section>

          <section className="briefing-controls" aria-label="情报简报筛选">
            <label>
              <span>选择球队</span>
              <select value={clubSlug} onChange={(event) => chooseClub(event.target.value)}>
                {clubs.map((club) => (
                  <option key={club.slug} value={club.slug}>{club.name}</option>
                ))}
              </select>
            </label>
            <label>
              <span>统一分钟门槛</span>
              <select
                value={minimumMinutes}
                onChange={(event) => chooseMinimumMinutes(Number(event.target.value))}
              >
                {minuteOptions.map((value) => (
                  <option key={value} value={value}>{value}+ 分钟</option>
                ))}
              </select>
            </label>
            <div>
              <span>本机偏好</span>
              <strong>已记住常用球队</strong>
            </div>
            <button type="button" onClick={() => window.print()} disabled={!data || loading}>
              打印 / 保存 PDF
            </button>
          </section>
        </div>

        {error && (
          <div className="match-page-state match-page-error briefing-screen-only" role="alert">
            <div><strong>球队情报简报读取失败</strong><p>请确认后端正在运行后重试。</p></div>
          </div>
        )}

        {data && (
          <article
            className={loading ? "briefing-document is-refreshing" : "briefing-document"}
            aria-busy={loading}
          >
            <header className="briefing-document-header" style={{ borderColor: data.club.primary_color }}>
              <div>
                <span>PLIA / CLUB FILE / {data.season}</span>
                <h2>{data.club.name}</h2>
                <p>{data.club.city} · {data.club.stadium_name}</p>
              </div>
              <div>
                <strong>#{String(data.season_summary.final_position).padStart(2, "0")}</strong>
                <span>FINAL POSITION</span>
              </div>
            </header>

            <section className="briefing-kpis" aria-label="球队赛季关键指标">
              <article><span>赛季积分</span><strong>{data.season_summary.overall.points}</strong><p>38 场最终积分</p></article>
              <article><span>净胜球</span><strong>{data.season_summary.overall.goal_difference > 0 ? "+" : ""}{data.season_summary.overall.goal_difference}</strong><p>{data.season_summary.overall.goals_for} 进 · {data.season_summary.overall.goals_against} 失</p></article>
              <article><span>末五场</span><strong>{data.season_summary.recent_points}<small>/15</small></strong><p>{data.season_summary.recent_form.join("-")}</p></article>
              <article><span>最长不败</span><strong>{data.season_summary.longest_unbeaten}</strong><p>连续场次</p></article>
              <article><span>前五负荷</span><strong>{data.squad.top_five_minutes_share.toFixed(1)}<small>%</small></strong><p>分析池分钟</p></article>
            </section>

            <section className="briefing-section briefing-season-section">
              <div className="briefing-section-heading">
                <span>01 / SEASON STATE</span>
                <h2>赛季状态</h2>
                <p>只由 2024–25 完整 380 场最终比分计算。</p>
              </div>
              <div className="briefing-record-grid">
                {[
                  ["整体", data.season_summary.overall],
                  ["主场", data.season_summary.home],
                  ["客场", data.season_summary.away],
                ].map(([label, record]) => {
                  const row = record as typeof data.season_summary.overall;
                  return (
                    <article key={label as string}>
                      <span>{label as string}</span>
                      <strong>{row.points}<small> 分</small></strong>
                      <p>{row.won} 胜 · {row.drawn} 平 · {row.lost} 负</p>
                      <footer>PPG {row.points_per_game.toFixed(2)}</footer>
                    </article>
                  );
                })}
                <article className="briefing-form-card">
                  <span>末五场时间序列</span>
                  <div>
                    {data.season_summary.recent_form.map((result, index) => (
                      <i className={`is-${result.toLowerCase()}`} key={`${result}-${index}`} title={resultLabels[result]}>{result}</i>
                    ))}
                  </div>
                  <p>按真实开球日期排序</p>
                </article>
              </div>
            </section>

            <section className="briefing-section">
              <div className="briefing-section-heading">
                <span>02 / SQUAD FRAME</span>
                <h2>阵容结构</h2>
                <p>{data.minimum_minutes}+ 分钟门槛 · {data.squad.qualified_total}/{data.squad.record_total} 条合格记录</p>
              </div>
              <div className="briefing-position-grid">
                {data.squad.position_groups.map((group) => (
                  <article key={group.position}>
                    <header><strong>{group.position}</strong><span>{group.label}</span></header>
                    <b>{group.minutes_share.toFixed(1)}%</b>
                    <div><i style={{ width: `${group.minutes_share}%` }} /></div>
                    <p>{formatNumber(group.minutes)} 分钟 · {group.goal_contributions} 次进球或助攻</p>
                  </article>
                ))}
              </div>
              <div className="briefing-leaders">
                {data.squad.leaders.map((leader) => (
                  <article key={leader.metric}>
                    <span>{leader.label}</span>
                    <strong>{leader.value}<small>{leader.unit}</small></strong>
                    <Link href={`/players/${leader.player.slug}`}>{leader.player.full_name}</Link>
                  </article>
                ))}
              </div>
            </section>

            <section className="briefing-section">
              <div className="briefing-section-heading">
                <span>03 / RECRUITMENT QUEUE</span>
                <h2>位置观察队列</h2>
                <p>三条队列独立计算；信号分不可跨位置当作能力总评。</p>
              </div>
              <div className="briefing-recruitment-grid">
                {data.recruitment.map((panel) => (
                  <article key={panel.position}>
                    <header>
                      <div><span>{panel.position}</span><h3>{panel.label}</h3></div>
                      <small>{panel.club_record_count} 队内 / {panel.peer_record_count} 同位置</small>
                    </header>
                    <div className="briefing-need-list">
                      {panel.needs.map((need) => (
                        <div key={need.key}>
                          <span>{need.label}</span><strong>P{need.club_percentile}</strong>
                          <i><b style={{ width: `${need.club_percentile}%` }} /></i>
                        </div>
                      ))}
                    </div>
                    {panel.top_candidate ? (
                      <div className="briefing-candidate">
                        <span>首位历史统计候选</span>
                        <Link href={`/players/${panel.top_candidate.slug}`}>{panel.top_candidate.full_name}</Link>
                        <p>{panel.top_candidate.club.short_name} · 信号 {panel.top_candidate.signal_score}/100 · 置信度 {panel.top_candidate.confidence_score}</p>
                      </div>
                    ) : (
                      <div className="briefing-candidate"><span>当前门槛无正向候选信号</span></div>
                    )}
                    <footer>
                      <p>{panel.note}</p>
                      <Link href={`/transfer?club=${data.club.slug}&position=${panel.position}`}>打开完整候选页 →</Link>
                    </footer>
                  </article>
                ))}
              </div>
            </section>

            <section className="briefing-section briefing-conclusion">
              <div className="briefing-section-heading">
                <span>04 / ANALYST NOTES</span>
                <h2>确定性摘要</h2>
                <p>每句话都可回到上方数据或来源进行核验。</p>
              </div>
              <ol>
                {data.headlines.map((headline, index) => (
                  <li key={headline}><span>{String(index + 1).padStart(2, "0")}</span><p>{headline}</p></li>
                ))}
              </ol>
            </section>

            <section className="briefing-boundary">
              <div>
                <span>GROUNDING CONTRACT</span>
                <h2>能说什么，也写清不能说什么。</h2>
              </div>
              <ul>{data.limitations.map((item) => <li key={item}>{item}</li>)}</ul>
            </section>

            <footer className="briefing-source-ledger">
              <div>
                <span>DATA LEDGER · SNAPSHOT {data.snapshot_date}</span>
                <p>{data.print_notice}</p>
              </div>
              <ol>
                {data.sources.map((source) => (
                  <li key={source.name}>
                    <a href={source.url} target="_blank" rel="noreferrer">{source.name}</a>
                    <span>{source.scope}</span>
                    <small>{source.license_name ?? "来源条款见原始页面"}</small>
                  </li>
                ))}
              </ol>
            </footer>
          </article>
        )}
      </div>
    </main>
  );
}
