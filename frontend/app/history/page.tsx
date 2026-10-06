"use client";
import { useEffect, useState } from "react";
import { SiteHeader } from "../../components/system/site-header";
import { hubRequest } from "../../services/hub";
import type { Archive, Forecast, SeasonInfo, Standing } from "../../services/hub";

const pct = (value: number) => `${(value * 100).toFixed(1)}%`;
export default function HistoryPage() {
  const [seasons, setSeasons] = useState<SeasonInfo[]>([]);
  const [season, setSeason] = useState("2024-25");
  const [archive, setArchive] = useState<Archive | null>(null);
  const [team, setTeam] = useState("");
  const [trend, setTrend] = useState<(Standing & { season: string })[]>([]);
  const [error, setError] = useState("");
  const [limit, setLimit] = useState(40);
  const [home, setHome] = useState("");
  const [away, setAway] = useState("");
  const [forecast, setForecast] = useState<Forecast | null>(null);
  const [predictError, setPredictError] = useState("");
  const [predicting, setPredicting] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    hubRequest<{ items: SeasonInfo[] }>("/hub/seasons", { signal: controller.signal }).then((data) => setSeasons(data.items)).catch((e) => { if (!controller.signal.aborted) setError(e.message); });
    return () => controller.abort();
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    hubRequest<Archive>(`/hub/history?season=${season}`, { signal: controller.signal }).then((data) => {
      setArchive(data); setError(""); setHome(data.standings[0]?.team ?? ""); setAway(data.standings[1]?.team ?? "");
    }).catch((e) => { if (!controller.signal.aborted) setError(e.message); });
    return () => controller.abort();
  }, [season]);
  useEffect(() => {
    if (!team) return;
    const controller = new AbortController();
    hubRequest<{ items: (Standing & { season: string })[] }>(`/hub/trend?team=${encodeURIComponent(team)}`, { signal: controller.signal }).then((data) => setTrend(data.items)).catch((e) => { if (!controller.signal.aborted) setError(e.message); });
    return () => controller.abort();
  }, [team]);
  async function predict() {
    setPredicting(true); setPredictError(""); setForecast(null);
    try { setForecast(await hubRequest<Forecast>(`/hub/prediction?${new URLSearchParams({ season, home, away })}`)); }
    catch (e) { setPredictError(e instanceof Error ? e.message : "预测请求失败"); }
    finally { setPredicting(false); }
  }
  const current = archive?.season === season ? archive : null;
  const matches = current?.matches.filter((m) => !team || team === m.team1 || team === m.team2) ?? [];
  return <main className="page-shell hub-shell"><SiteHeader />
    <header className="hub-title"><p className="eyebrow">SEASON ARCHIVE</p><h1>让每个赛季，成为参照。</h1><p>切换历史赛季，查看赛果、积分与球队跨赛季变化。</p></header>
    <div className="hub-controls"><label>赛季<select disabled={predicting} value={season} onChange={(e) => { setSeason(e.target.value); setTeam(""); setTrend([]); setLimit(40); setForecast(null); setPredictError(""); setError(""); }}>
      {seasons.length ? seasons.map((s) => <option key={s.season} value={s.season}>{s.season} · 已录入 {s.played}/{s.matches} 场赛果</option>) : <option>{season}</option>}</select></label>
      <label>球队<select value={team} onChange={(e) => { setTeam(e.target.value); setTrend([]); setLimit(40); }}><option value="">全部球队</option>{current?.standings.map((s) => <option key={s.team}>{s.team}</option>)}</select></label></div>
    {error && <p role="alert" className="hub-error">{error}</p>}
    {!current && !error && <p role="status">正在读取赛季档案…</p>}
    {current && <><p className="hub-meta">档案更新：{new Date(current.fetched_at).toLocaleString()} · <a href={current.source_url} target="_blank" rel="noreferrer">OpenFootball 原始来源 ↗</a></p>
      <div className="hub-stats"><div><strong>{current.matches.filter((m) => m.score?.ft).length}</strong><span>已录入赛果</span></div><div><strong>{current.standings.length}</strong><span>参赛球队</span></div><div><strong>{current.standings.reduce((n, r) => n + r.goals_for, 0)}</strong><span>总进球</span></div></div>
      {team && <section className="hub-panel"><h2>{team} · 跨赛季对比</h2><div className="hub-table-wrap"><table><thead><tr><th>赛季</th><th>当前排名</th><th>场次</th><th>积分</th><th>场均积分</th><th>进球</th><th>失球</th></tr></thead><tbody>{trend.map((r) => <tr key={r.season}><td>{r.season}</td><td>{r.rank}</td><td>{r.played}</td><td>{r.points}</td><td>{r.played ? (r.points/r.played).toFixed(2) : "—"}</td><td>{r.goals_for}</td><td>{r.goals_against}</td></tr>)}</tbody></table></div><p className="hub-meta">缺席英超的赛季不填零；进行中或缺少赛果的赛季按已录入场次统计。</p></section>}
      <div className="hub-columns"><section className="hub-panel"><h2>积分对照</h2><div className="hub-table-wrap"><table><thead><tr><th>#</th><th>球队</th><th>场次</th><th>胜/平/负</th><th>净胜球</th><th>积分</th></tr></thead><tbody>{current.standings.map((r) => <tr key={r.team}><td>{r.rank}</td><td><button className="hub-text-button" onClick={() => {if (team !== r.team) {setTeam(r.team); setTrend([]);}}}>{r.team}</button></td><td>{r.played}</td><td>{r.won}/{r.drawn}/{r.lost}</td><td>{r.goal_difference}</td><td><strong>{r.points}</strong></td></tr>)}</tbody></table></div><p className="hub-meta">{current.notice}</p></section>
      <section className="hub-panel"><h2>赛程与结果 · {matches.length} 场</h2><div className="hub-match-list">{matches.slice(0, limit).map((m) => <article key={`${m.date}:${m.team1}:${m.team2}`}><small>{m.date} · {m.round}</small><div><span>{m.team1}</span><strong>{m.score?.ft?.join(" : ") ?? "待赛"}</strong><span>{m.team2}</span></div></article>)}</div>{limit < matches.length && <button className="secondary-button" onClick={() => setLimit(limit+40)}>加载更多</button>}</section></div>
      <section className="hub-panel"><h2>比赛结果预测</h2><p className="hub-meta">基于所选赛季进失球的泊松基线，用于比较概率；支持的球队来自所选赛季。</p><div className="hub-controls"><label>主队<select value={home} disabled={predicting} onChange={(e) => {setHome(e.target.value); setForecast(null);}}>{current.standings.map((r) => <option key={r.team}>{r.team}</option>)}</select></label><label>客队<select value={away} disabled={predicting} onChange={(e) => {setAway(e.target.value); setForecast(null);}}>{current.standings.map((r) => <option key={r.team}>{r.team}</option>)}</select></label><button className="primary-button" disabled={!home || !away || home === away || predicting} onClick={predict}>{predicting ? "计算中…" : "计算胜平负概率"}</button></div>
      {predictError && <p role="alert" className="hub-error">{predictError}</p>}{forecast && <><div className="hub-stats"><div><strong>{pct(forecast.home_win)}</strong><span>主胜</span></div><div><strong>{pct(forecast.draw)}</strong><span>平局</span></div><div><strong>{pct(forecast.away_win)}</strong><span>客胜</span></div></div><p>概率较高的比分：{forecast.scorelines.map((s) => `${s.score}（${pct(s.probability)}）`).join(" · ")}</p><p className="hub-meta">截止 {forecast.before} 前，联赛 {forecast.sample_matches} 场；主队主场 {forecast.home_samples} 场，客队客场 {forecast.away_samples} 场。{forecast.notice}</p></>}</section>
    </>}
  </main>;
}
