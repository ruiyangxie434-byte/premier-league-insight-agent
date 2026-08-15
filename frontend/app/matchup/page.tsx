"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { SiteHeader } from "../../components/system/site-header";
import { getClubMatchup, getSeasonForm } from "../../services/api";
import type { ClubMatchupData, FormResult, SeasonFormClubItem } from "../../types/api";

const resultLabels: Record<FormResult, string> = { W: "胜", D: "平", L: "负" };

function FormStrip({ results }: { results: FormResult[] }) {
  return <span className="matchup-form-strip" aria-label={results.map((item) => resultLabels[item]).join("、")}>{results.map((item, index) => <i data-result={item} key={`${item}-${index}`}>{item}</i>)}</span>;
}

function formatDate(value: string | null) {
  if (!value) return "日期未知";
  return new Intl.DateTimeFormat("zh-CN", { year: "numeric", month: "short", day: "numeric" }).format(new Date(value));
}

export default function MatchupPage() {
  const [clubs, setClubs] = useState<SeasonFormClubItem[]>([]);
  const [clubA, setClubA] = useState("liverpool");
  const [clubB, setClubB] = useState("arsenal");
  const [data, setData] = useState<ClubMatchupData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    getSeasonForm("2024-25", controller.signal).then((response) => setClubs(response.data?.items ?? [])).catch(() => undefined);
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    getClubMatchup(clubA, clubB, "2024-25", controller.signal)
      .then((response) => {
        if (!response.data) throw new Error("对阵数据为空");
        setData(response.data);
      })
      .catch(() => { if (!controller.signal.aborted) setError(true); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [clubA, clubB]);

  function chooseA(next: string) {
    setLoading(true);
    setError(false);
    if (next === clubB) setClubB(clubA);
    setClubA(next);
  }
  function chooseB(next: string) {
    setLoading(true);
    setError(false);
    if (next === clubA) setClubA(clubB);
    setClubB(next);
  }

  function swapClubs() {
    setLoading(true);
    setError(false);
    setClubA(clubB);
    setClubB(clubA);
  }

  return <main className="matchup-page"><div className="page-shell matchup-shell">
    <SiteHeader />
    <Link className="club-back-link" href="/form"><span aria-hidden="true">←</span>返回赛季状态实验室</Link>
    <section className="matchup-hero"><div><p className="eyebrow">MATCHUP LAB · NO PREDICTION</p><h1>两支球队，<span>八个真实维度。</span></h1><p>用 2024–25 完整赛果拆解排名、攻防、主客场、近期状态与直接交锋。只复盘已经发生的比赛，不生成伪胜率。</p></div><div className="matchup-hero-mark"><span>HISTORICAL</span><strong>8</strong><small>COMPARISON AXES</small></div></section>

    <section className="matchup-picker" aria-label="选择对阵球队">
      <label><span>球队 A</span><select value={clubA} onChange={(event) => chooseA(event.target.value)}>{clubs.map((item) => <option key={item.club.slug} value={item.club.slug}>{item.club.name}</option>)}</select></label>
      <button type="button" onClick={swapClubs} aria-label="交换两支球队">⇄</button>
      <label><span>球队 B</span><select value={clubB} onChange={(event) => chooseB(event.target.value)}>{clubs.map((item) => <option key={item.club.slug} value={item.club.slug}>{item.club.name}</option>)}</select></label>
      <small>{loading ? "正在重新计算…" : "数据来自固定历史快照"}</small>
    </section>

    {error && <div className="match-page-state match-page-error"><div><strong>对阵数据读取失败</strong><p>请确认后端仍在运行后重试。</p></div></div>}
    {data && <div className={loading ? "matchup-content is-refreshing" : "matchup-content"}>
      <section className="matchup-scoreboard">
        {[data.club_a, data.club_b].map((item, index) => <article key={item.club.slug} style={{ "--club-color": item.club.primary_color } as React.CSSProperties}>
          <span>CLUB {index === 0 ? "A" : "B"} · FINAL #{item.final_position}</span><h2>{item.club.name}</h2><strong>{item.overall.points}<small> 分</small></strong><dl><div><dt>进 / 失</dt><dd>{item.overall.goals_for} / {item.overall.goals_against}</dd></div><div><dt>主 / 客积分</dt><dd>{item.home.points} / {item.away.points}</dd></div><div><dt>最长不败</dt><dd>{item.longest_unbeaten} 场</dd></div></dl><FormStrip results={item.recent_form} />
        </article>)}
      </section>

      <section className="matchup-matrix"><div className="section-heading"><div><p className="eyebrow">COMPARISON MATRIX</p><h2>确定性优势矩阵</h2></div><p>绿色标记只代表该历史统计维度占优，不等于未来对阵优势。</p></div>
        <div className="matchup-matrix-grid">{data.dimensions.map((item) => <article key={item.key}><strong data-advantage={item.advantage === "club_a"}>{item.club_a_value}</strong><div><span>{item.label}</span><small>{item.note}</small></div><strong data-advantage={item.advantage === "club_b"}>{item.club_b_value}</strong></article>)}</div>
      </section>

      <section className="matchup-meetings"><div><p className="eyebrow">HEAD TO HEAD · 2024–25</p><h2>赛季两回合</h2><strong>{data.club_a.club.short_name} {data.head_to_head.club_a_goals}–{data.head_to_head.club_b_goals} {data.club_b.club.short_name}</strong><small>总比分仅汇总本赛季两场联赛</small></div><ol>{data.head_to_head.meetings.map((match) => <li key={match.source_match_id}><span>MW {match.matchweek}<small>{formatDate(match.kickoff_at)}</small></span><div><b>{match.home_club.short_name}</b><strong>{match.home_score}–{match.away_score}</strong><b>{match.away_club.short_name}</b></div></li>)}</ol></section>

      <section className="matchup-brief"><div><p className="eyebrow">GROUNDED BRIEF</p><h2>对阵结论边界</h2></div><ul>{data.summary.map((item) => <li key={item}>{item}</li>)}</ul><footer><span>{data.source_name} · {data.snapshot_date}</span><Link href="/evidence">查看完整数据证据 →</Link></footer></section>
    </div>}
  </div></main>;
}
