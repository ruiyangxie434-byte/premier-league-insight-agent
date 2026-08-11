"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useState } from "react";

import { getMatches } from "../../services/api";
import type { MatchListData } from "../../types/api";

type PageState = "loading" | "success" | "error";

function formatMatchDate(value: string | null) {
  if (!value) {
    return "日期待确认";
  }
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date(value));
}

export default function MatchesPage() {
  const [state, setState] = useState<PageState>("loading");
  const [data, setData] = useState<MatchListData | null>(null);
  const [requestId, setRequestId] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    async function loadMatches() {
      setState("loading");
      try {
        const response = await getMatches(controller.signal);
        if (!response.data) {
          throw new Error("比赛快照为空");
        }
        setData(response.data);
        setState("success");
      } catch {
        if (!controller.signal.aborted) {
          setState("error");
        }
      }
    }

    void loadMatches();
    return () => controller.abort();
  }, [requestId]);

  return (
    <main>
      <div className="page-shell match-list-shell">
        <header className="site-header">
          <Link className="brand" href="/" aria-label="英超智析 Agent 首页">
            <span className="brand-mark" aria-hidden="true">AI</span>
            <span>
              <strong>英超智析 Agent</strong>
              <small>Premier League Insight Agent</small>
            </span>
          </Link>
          <span className="phase-badge">v0.12.0 · Player Intelligence Atlas</span>
        </header>

        <Link className="club-back-link" href="/">
          <span aria-hidden="true">←</span>
          返回地图首页
        </Link>

        <section className="match-list-hero" aria-labelledby="match-list-title">
          <div>
            <p className="eyebrow">MATCH LAB · OPEN EVENT DATA</p>
            <h1 id="match-list-title">
              从比分走进，
              <span>每一次射门。</span>
            </h1>
            <p>
              使用可追溯的公开事件数据，把比赛结果拆成射门位置、机会质量与进球时间线；先理解发生了什么，再解释为什么。
            </p>
          </div>
          <div className="match-pipeline" aria-label="比赛数据处理流程">
            <div><span>01</span><strong>RAW JSON</strong><small>来源文件</small></div>
            <i aria-hidden="true">→</i>
            <div><span>02</span><strong>NORMALIZE</strong><small>坐标清洗</small></div>
            <i aria-hidden="true">→</i>
            <div><span>03</span><strong>EXPLAIN</strong><small>可视化解释</small></div>
          </div>
        </section>

        {state === "loading" && (
          <div className="match-page-state" aria-live="polite">
            <span className="loading-ring" aria-hidden="true" />
            <div>
              <strong>正在读取历史比赛快照</strong>
              <p>从 FastAPI 聚合比赛、球队与射门事件。</p>
            </div>
          </div>
        )}

        {state === "error" && (
          <div className="match-page-state match-page-error" role="alert">
            <div>
              <span>MATCH DATA OFFLINE</span>
              <strong>暂时无法读取比赛快照</strong>
              <p>请确认后端仍在运行，再重新加载。</p>
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
          <>
            <section className="featured-match-section" aria-labelledby="featured-match-title">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">FEATURED SNAPSHOT</p>
                  <h2 id="featured-match-title">公开比赛样例</h2>
                </div>
                <p>{data.sample_notice}</p>
              </div>

              <div className="featured-match-grid">
                {data.items.map((match) => (
                  <Link
                    className="featured-match-card"
                    href={`/matches/${match.source_match_id}`}
                    key={match.source_match_id}
                  >
                    <div className="featured-match-meta">
                      <span>{match.competition} · {match.season}</span>
                      <time dateTime={match.kickoff_at ?? undefined}>
                        {formatMatchDate(match.kickoff_at)}
                      </time>
                    </div>
                    <div className="featured-scoreboard">
                      <div>
                        <i style={{ background: match.home_team.primary_color }} />
                        <strong>{match.home_team.short_name}</strong>
                        <small>{match.home_team.shots} 射门 · {match.home_team.total_xg.toFixed(2)} xG</small>
                      </div>
                      <span>{match.home_team.score}</span>
                      <b>—</b>
                      <span>{match.away_team.score}</span>
                      <div>
                        <i style={{ background: match.away_team.primary_color }} />
                        <strong>{match.away_team.short_name}</strong>
                        <small>{match.away_team.shots} 射门 · {match.away_team.total_xg.toFixed(2)} xG</small>
                      </div>
                    </div>
                    <div className="featured-match-footer">
                      <span>{match.venue} · 第 {match.matchweek} 轮</span>
                      <strong>打开 28 次射门 →</strong>
                    </div>
                  </Link>
                ))}
              </div>
            </section>

            <aside className="match-source-strip">
              <div>
                <span>DATA SOURCE</span>
                <Image
                  className="statsbomb-logo"
                  src="/statsbomb-open-data.png"
                  alt="StatsBomb"
                  width={150}
                  height={24}
                />
              </div>
              <p>页面只使用公开历史快照，来源、许可与解释边界均随 API 返回。</p>
              <div>
                <a href={data.source_url} target="_blank" rel="noreferrer">查看数据仓库 ↗</a>
                <a href={data.license_url} target="_blank" rel="noreferrer">查看许可 ↗</a>
              </div>
            </aside>
          </>
        )}
      </div>
    </main>
  );
}
