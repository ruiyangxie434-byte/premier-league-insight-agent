"use client";
import { useEffect, useRef, useState } from "react";
import { SiteHeader } from "../../components/system/site-header";
import { getApiBaseUrl } from "../../services/api";
import { hubRequest } from "../../services/hub";
import type { Feed, Fixture, Injury, Lineup, NewsItem, ProviderTeam, Squad, Transfer } from "../../services/hub";

type Updates = { kind: "squad"; data: Feed<Squad> } | { kind: "transfers"; data: Feed<Transfer> } | { kind: "injuries"; data: Feed<Injury> } | { kind: "lineups"; data: Feed<Lineup> };
const kindLabels = { squad: "现役阵容", transfers: "转会记录", injuries: "伤病与停赛", lineups: "比赛首发" };
function FeedStatus({ feed }: { feed: Feed<unknown> | null }) {
  if (!feed) return <p className="hub-meta" role="status">正在连接数据源…</p>;
  return <p className="hub-meta" role="status">{feed.source} · {feed.status === "stale" ? "缓存数据" : feed.status === "ok" ? "已更新" : "暂不可用"}
    {feed.updated_at && ` · ${new Date(feed.updated_at).toLocaleString()}`}{feed.message && ` · ${feed.message}`}
    {feed.status === "ok" && !feed.items.length && " · 数据源当前没有返回记录"}</p>;
}
function FixtureCards({ items, select }: { items: Fixture[]; select: (id: number) => void }) {
  return <div className="fixture-grid">{items.map((m) => <article className="fixture-card" key={m.fixture.id}>
    <small>{new Date(m.fixture.date).toLocaleString()} · {m.fixture.status.short} {m.fixture.status.elapsed != null ? `${m.fixture.status.elapsed}′` : ""}</small>
    <div><span>{m.teams.home.name}</span><strong>{m.goals.home ?? "—"} : {m.goals.away ?? "—"}</strong><span>{m.teams.away.name}</span></div>
    <button className="hub-text-button" onClick={() => select(m.fixture.id)}>查看首发与替补 ↗</button>
  </article>)}</div>;
}
function UpdateContent({ updates }: { updates: Updates }) {
  switch (updates.kind) {
    case "squad": return <div className="hub-table-wrap"><table><thead><tr><th>球员</th><th>号码</th><th>位置</th><th>年龄</th></tr></thead><tbody>{updates.data.items.flatMap((s) => s.players.map((p) => <tr key={`${s.team.id}:${p.id}`}><td>{p.name}</td><td>{p.number ?? "—"}</td><td>{p.position}</td><td>{p.age ?? "—"}</td></tr>))}</tbody></table></div>;
    case "transfers": return <div className="hub-table-wrap"><table><thead><tr><th>日期</th><th>球员</th><th>离队</th><th>加盟</th><th>类型</th></tr></thead><tbody>{updates.data.items.flatMap((p) => p.transfers.map((t, i) => ({ player: p.player, transfer: t, index: i }))).sort((a,b) => b.transfer.date.localeCompare(a.transfer.date)).slice(0,100).map(({ player, transfer: t, index }) => <tr key={`${player.id}:${t.date}:${index}`}><td>{t.date}</td><td>{player.name}</td><td>{t.teams.out?.name ?? "—"}</td><td>{t.teams.in?.name ?? "—"}</td><td>{t.type}</td></tr>)}</tbody></table></div>;
    case "injuries": return <div className="hub-table-wrap"><table><thead><tr><th>球员</th><th>类型</th><th>原因</th><th>对应比赛</th></tr></thead><tbody>{updates.data.items.slice(0,100).map((r) => <tr key={`${r.player.id}:${r.fixture.id}`}><td>{r.player.name}</td><td>{r.player.type}</td><td>{r.player.reason}</td><td>{new Date(r.fixture.date).toLocaleDateString()}</td></tr>)}</tbody></table></div>;
    case "lineups": return <div className="hub-columns">{updates.data.items.map((r) => <article key={r.team.id}><h3>{r.team.name} · {r.formation ?? "阵型待公布"}</h3><h4>首发</h4><ul>{r.startXI.map(({ player: p }) => <li key={p.id}>{p.number ?? "—"} · {p.name} · {p.pos}</li>)}</ul><h4>替补</h4><ul>{r.substitutes.map(({ player: p }) => <li key={p.id}>{p.number ?? "—"} · {p.name}</li>)}</ul></article>)}</div>;
  }
}
export default function LivePage() {
  const now = new Date();
  const thisSeason = now.getFullYear() - (now.getMonth() < 7 ? 1 : 0);
  const [season, setSeason] = useState(thisSeason);
  const [day, setDay] = useState(`${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,"0")}-${String(now.getDate()).padStart(2,"0")}`);
  const [fixtures, setFixtures] = useState<Feed<Fixture> | null>(null);
  const [live, setLive] = useState<Feed<Fixture> | null>(null);
  const [news, setNews] = useState<Feed<NewsItem> | null>(null);
  const [teams, setTeams] = useState<Feed<{ team: ProviderTeam }> | null>(null);
  const [team, setTeam] = useState("");
  const [fixture, setFixture] = useState<number | null>(null);
  const [kind, setKind] = useState<Updates["kind"]>("squad");
  const [updates, setUpdates] = useState<Updates | null>(null);
  const [error, setError] = useState("");
  const [subscribe, setSubscribe] = useState(false);
  const [pushMessage, setPushMessage] = useState("");
  const [refresh, setRefresh] = useState(0);
  const scoreSnapshot = useRef<string | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    const options = { signal: controller.signal };
    Promise.allSettled([
      hubRequest<Feed<NewsItem>>("/hub/news", options).then(setNews),
      hubRequest<Feed<Fixture>>("/hub/live", options).then(setLive),
    ]).then((results) => { if (!controller.signal.aborted && results.some((r) => r.status === "rejected")) setError("部分数据请求失败，请点击刷新重试。"); });
    return () => controller.abort();
  }, [refresh]);
  useEffect(() => {
    const controller = new AbortController();
    hubRequest<Feed<{ team: ProviderTeam }>>(`/hub/teams?season=${season}`, { signal: controller.signal }).then((data) => { setTeams(data); setTeam(data.items[0] ? String(data.items[0].team.id) : ""); }).catch((e) => { if (!controller.signal.aborted) setError(e.message); });
    return () => controller.abort();
  }, [season, refresh]);
  useEffect(() => {
    const controller = new AbortController();
    hubRequest<Feed<Fixture>>(`/hub/fixtures?${new URLSearchParams({ season: String(season), day })}`, { signal: controller.signal }).then(setFixtures).catch((e) => { if (!controller.signal.aborted) setError(e.message); });
    return () => controller.abort();
  }, [season, day, refresh]);
  useEffect(() => {
    if ((kind === "lineups" && !fixture) || (kind !== "lineups" && !team)) return;
    const controller = new AbortController();
    const path = `/hub/updates?${new URLSearchParams({ kind, season: String(season), ...(kind === "lineups" ? { fixture: String(fixture) } : { team }) })}`;
    const options = { signal: controller.signal };
    const request = kind === "squad" ? hubRequest<Feed<Squad>>(path, options).then((data) => setUpdates({ kind, data }))
      : kind === "transfers" ? hubRequest<Feed<Transfer>>(path, options).then((data) => setUpdates({ kind, data }))
      : kind === "injuries" ? hubRequest<Feed<Injury>>(path, options).then((data) => setUpdates({ kind, data }))
      : hubRequest<Feed<Lineup>>(path, options).then((data) => setUpdates({ kind, data }));
    request.catch((e) => { if (!controller.signal.aborted) setError(e.message); });
    return () => controller.abort();
  }, [kind, team, fixture, season, refresh]);
  useEffect(() => {
    if (!subscribe) return;
    const stream = new EventSource(`${getApiBaseUrl()}/hub/live/stream`, { withCredentials: true });
    stream.onmessage = (event) => {
      const data = JSON.parse(event.data) as Feed<Fixture>;
      setLive(data);
      if (data.status === "not_configured") { stream.close(); setSubscribe(false); setPushMessage("实时数据源尚未配置。"); return; }
      if (data.status !== "ok") { setPushMessage(data.message ?? "数据源暂不可用"); return; }
      const score = JSON.stringify(data.items.map((m) => [m.fixture.id, m.goals.home, m.goals.away]).sort((a,b) => Number(a[0])-Number(b[0])));
      if (scoreSnapshot.current !== null && score !== scoreSnapshot.current) setPushMessage(`比分或进行中的比赛已更新：${new Date().toLocaleTimeString()}`);
      else setPushMessage(`推送已连接 · ${new Date().toLocaleTimeString()}`);
      scoreSnapshot.current = score;
    };
    stream.onerror = () => { setPushMessage("比分连接中断，正在自动重连…"); };
    return () => stream.close();
  }, [subscribe]);
  function selectFixture(id: number) { if (fixture !== id || kind !== "lineups") { setFixture(id); setKind("lineups"); setUpdates(null); } document.getElementById("team-updates")?.scrollIntoView({ behavior: "smooth" }); }
  return <main className="page-shell hub-shell"><SiteHeader />
    <header className="hub-title"><p className="eyebrow">MATCH CENTRE</p><h1>今天的英超，一站看清。</h1><p>赛程、比分、新闻和球队动态，保留来源与更新时间。</p></header>
    <div className="hub-controls"><label>赛季<select value={season} onChange={(e) => {setSeason(Number(e.target.value)); setTeams(null); setTeam(""); setFixtures(null); setUpdates(null); setFixture(null);}}>{Array.from({length:6}, (_,i) => thisSeason-i).map((y) => <option key={y} value={y}>{y}–{String(y+1).slice(-2)}</option>)}</select></label><label>比赛日期<input type="date" required value={day} onChange={(e) => { if (e.target.value) {setDay(e.target.value); setFixtures(null); setFixture(null); setUpdates(null);} }} /></label><button className="secondary-button" onClick={() => {setError(""); setUpdates(null); setRefresh(refresh+1);}}>刷新数据</button></div>
    {error && <p className="hub-error" role="alert">{error}</p>}
    <section className="hub-panel"><div className="hub-section-heading"><h2>进行中的比赛</h2><button className="primary-button" aria-pressed={subscribe} onClick={() => {scoreSnapshot.current=null; setSubscribe(!subscribe); setPushMessage(!subscribe ? "正在连接推送…" : "推送已暂停");}}>{subscribe ? "暂停比分推送" : "开启比分推送"}</button></div>
      <p className="hub-meta">比分推送在此页面打开期间有效。更新速度取决于数据源与服务器刷新间隔。</p><p role="status" aria-live="polite">{pushMessage}</p><FeedStatus feed={live} />{live && <FixtureCards items={live.items} select={selectFixture} />}</section>
    <section className="hub-panel"><h2>当日赛程与赛果</h2><FeedStatus feed={fixtures} />{fixtures && <FixtureCards items={fixtures.items} select={selectFixture} />}</section>
    <section className="hub-panel" id="team-updates"><h2>球队动态</h2><FeedStatus feed={teams} />
      <div className="hub-controls"><label>球队<select value={team} onChange={(e) => {setTeam(e.target.value); setUpdates(null);}}><option value="">请选择球队</option>{teams?.items.map(({team: t}) => <option key={t.id} value={t.id}>{t.name}</option>)}</select></label></div>
      <div className="hub-tabs">{(Object.keys(kindLabels) as Updates["kind"][]).map((k) => <button key={k} aria-pressed={kind === k} onClick={() => {if (kind !== k) {setKind(k); setUpdates(null);}}}>{kindLabels[k]}</button>)}</div>
      {kind === "lineups" && !fixture ? <p className="hub-meta">先在赛程或实时比分卡片中选择一场比赛；开赛前尚未公布首发时会返回空记录。</p> : !team && kind !== "lineups" ? <p className="hub-meta">请选择已接入数据源的球队。</p> : <><FeedStatus feed={updates?.data ?? null} />{updates && <UpdateContent updates={updates} />}</>}
      <p className="hub-meta">阵容是数据源的现役名单，伤病按所选赛季返回，转会显示球队历史记录（最新 100 条）；并非每分钟更新。</p></section>
    <section className="hub-panel"><h2>足球新闻</h2><FeedStatus feed={news} /><div className="news-grid">{news?.items.map((item) => <a className="news-card" href={item.url} key={item.url} target="_blank" rel="noreferrer"><small>{item.source} · {new Date(item.published_at).toLocaleString()}</small><h3>{item.title}</h3><span>阅读原文 ↗</span></a>)}</div><p className="hub-meta">BBC Sport 足球频道标题与原文链接，包含英超及其他足球赛事。</p></section>
  </main>;
}
