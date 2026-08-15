"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { PointsTrendChart } from "../../components/form/points-trend-chart";
import { SiteHeader } from "../../components/system/site-header";
import { getSeasonForm } from "../../services/api";
import type {
  FormResult,
  SeasonFormClubItem,
  SeasonFormOverviewData,
} from "../../types/api";

type PageState = "loading" | "success" | "error";

const resultLabels: Record<FormResult, string> = {
  W: "胜",
  D: "平",
  L: "负",
};

function FormChips({ results }: { results: FormResult[] }) {
  return (
    <span className="form-chip-row" aria-label={`近五场：${results.map((result) => resultLabels[result]).join("、")}`}>
      {results.map((result, index) => (
        <i data-result={result} key={`${result}-${index}`}>
          {result}
        </i>
      ))}
    </span>
  );
}

function ClubCompareCard({ item }: { item: SeasonFormClubItem }) {
  return (
    <article className="form-compare-card">
      <div>
        <i style={{ background: item.club.primary_color }} />
        <span>第 {item.position} 名</span>
      </div>
      <h3>{item.club.name}</h3>
      <strong>{item.overall.points}<small> 分</small></strong>
      <dl>
        <div><dt>主场</dt><dd>{item.home.won}胜 · {item.home.points}分</dd></div>
        <div><dt>客场</dt><dd>{item.away.won}胜 · {item.away.points}分</dd></div>
        <div><dt>末五场</dt><dd>{item.recent_points}分</dd></div>
      </dl>
      <FormChips results={item.recent_form} />
    </article>
  );
}

export default function SeasonFormPage() {
  const [state, setState] = useState<PageState>("loading");
  const [data, setData] = useState<SeasonFormOverviewData | null>(null);
  const [primarySlug, setPrimarySlug] = useState("liverpool");
  const [comparisonSlug, setComparisonSlug] = useState("arsenal");
  const [requestId, setRequestId] = useState(0);

  function selectPrimary(nextSlug: string) {
    if (nextSlug === comparisonSlug) {
      setComparisonSlug(primarySlug);
    }
    setPrimarySlug(nextSlug);
  }

  function selectComparison(nextSlug: string) {
    if (nextSlug === primarySlug) {
      setPrimarySlug(comparisonSlug);
    }
    setComparisonSlug(nextSlug);
  }

  useEffect(() => {
    const controller = new AbortController();

    async function loadForm() {
      setState("loading");
      try {
        const response = await getSeasonForm("2024-25", controller.signal);
        if (!response.data) {
          throw new Error("赛季状态数据为空");
        }
        setData(response.data);
        setState("success");
      } catch {
        if (!controller.signal.aborted) {
          setState("error");
        }
      }
    }

    void loadForm();
    return () => controller.abort();
  }, [requestId]);

  const selectedClubs = useMemo(() => {
    if (!data) {
      return [];
    }
    const slugs = [primarySlug, comparisonSlug];
    return slugs
      .map((slug) => data.items.find((item) => item.club.slug === slug))
      .filter((item): item is SeasonFormClubItem => Boolean(item))
      .filter((item, index, items) =>
        items.findIndex((candidate) => candidate.club.slug === item.club.slug) === index,
      );
  }, [comparisonSlug, data, primarySlug]);

  return (
    <main>
      <div className="page-shell form-page-shell">
        <SiteHeader />

        <Link className="club-back-link" href="/">
          <span aria-hidden="true">←</span>
          返回地图首页
        </Link>
        <Link className="secondary-button form-matchup-link" href="/matchup">
          打开 Matchup Lab →
        </Link>

        <section className="form-hero" aria-labelledby="form-page-title">
          <div>
            <p className="eyebrow">SEASON FORM LAB · 380 RESULTS</p>
            <h1 id="form-page-title">
              一整个赛季，
              <span>不只是一张积分榜。</span>
            </h1>
            <p>
              把 2024–25 英超 380 场最终比分重新组织成积分轨迹、主客场拆分与末五场状态，观察球队如何走到最终排名。
            </p>
          </div>
          <div className="form-hero-stamp" aria-hidden="true">
            <span>2024</span>
            <strong>38</strong>
            <small>MATCHWEEKS</small>
          </div>
        </section>

        {state === "loading" && (
          <div className="match-page-state" aria-live="polite">
            <span className="loading-ring" aria-hidden="true" />
            <div>
              <strong>正在重建 2024–25 赛季轨迹</strong>
              <p>读取 380 场比分并计算 20 支球队的累计积分。</p>
            </div>
          </div>
        )}

        {state === "error" && (
          <div className="match-page-state match-page-error" role="alert">
            <div>
              <span>FORM DATA OFFLINE</span>
              <strong>暂时无法读取赛季状态</strong>
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
            <section className="form-summary-grid" aria-label="赛季摘要">
              <article><span>RESULTS</span><strong>{data.match_count}</strong><small>场完整赛果</small></article>
              <article><span>GOALS</span><strong>{data.goal_count}</strong><small>{data.goals_per_match} 球 / 场</small></article>
              <article><span>HOME WINS</span><strong>{data.home_wins}</strong><small>{Math.round(data.home_wins / data.match_count * 100)}% 比赛</small></article>
              <article><span>DRAWS</span><strong>{data.draws}</strong><small>{data.away_wins} 场客胜</small></article>
            </section>

            <section className="form-trend-section" aria-labelledby="form-trend-title">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">POINTS TRAJECTORY</p>
                  <h2 id="form-trend-title">38 轮积分走势</h2>
                </div>
                <p>选择两支球队，对比每一轮结束后的累计积分；延期比赛仍归回原比赛轮次。</p>
              </div>

              <div className="form-selector-row">
                <label>
                  <span>球队 A</span>
                  <select value={primarySlug} onChange={(event) => selectPrimary(event.target.value)}>
                    {data.items.map((item) => (
                      <option value={item.club.slug} key={item.club.slug}>{item.club.name}</option>
                    ))}
                  </select>
                </label>
                <span aria-hidden="true">VS</span>
                <label>
                  <span>球队 B</span>
                  <select value={comparisonSlug} onChange={(event) => selectComparison(event.target.value)}>
                    {data.items.map((item) => (
                      <option value={item.club.slug} key={item.club.slug}>{item.club.name}</option>
                    ))}
                  </select>
                </label>
              </div>

              <div className="form-trend-layout">
                <PointsTrendChart clubs={selectedClubs} />
                <div className="form-compare-grid">
                  {selectedClubs.map((item) => (
                    <ClubCompareCard item={item} key={item.club.slug} />
                  ))}
                </div>
              </div>
            </section>

            <section className="form-table-section" aria-labelledby="form-table-title">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">FINAL TABLE · LAST FIVE</p>
                  <h2 id="form-table-title">20 队赛季状态</h2>
                </div>
                <p>末五场按真实开球日期排序；点击球队可将它带入上方积分走势。</p>
              </div>
              <div className="form-table-scroll">
                <table className="form-table">
                  <thead>
                    <tr>
                      <th>排名</th><th>球队</th><th>赛</th><th>胜</th><th>平</th><th>负</th>
                      <th>进/失</th><th>净胜</th><th>积分</th><th>末五场</th><th>末五场分</th><th />
                    </tr>
                  </thead>
                  <tbody>
                    {data.items.map((item) => (
                      <tr key={item.club.slug} data-selected={selectedClubs.some((club) => club.club.slug === item.club.slug)}>
                        <td><strong>{item.position}</strong></td>
                        <td>
                          <button type="button" onClick={() => selectPrimary(item.club.slug)}>
                            <i style={{ background: item.club.primary_color }} />
                            <span>{item.club.name}</span>
                          </button>
                        </td>
                        <td>{item.overall.played}</td><td>{item.overall.won}</td><td>{item.overall.drawn}</td><td>{item.overall.lost}</td>
                        <td>{item.overall.goals_for}/{item.overall.goals_against}</td>
                        <td>{item.overall.goal_difference > 0 ? "+" : ""}{item.overall.goal_difference}</td>
                        <td><strong>{item.overall.points}</strong></td>
                        <td><FormChips results={item.recent_form} /></td>
                        <td>{item.recent_points}</td>
                        <td><Link href={`/clubs/${item.club.slug}`}>球队页 →</Link></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            <aside className="form-source-strip">
              <div><span>DATA SOURCE</span><strong>{data.source_name}</strong></div>
              <p>{data.sample_notice}</p>
              <div>
                <a href={data.source_url} target="_blank" rel="noreferrer">固定数据文件 ↗</a>
                <a href={data.license_url} target="_blank" rel="noreferrer">{data.license_name} ↗</a>
                <code>{data.source_commit.slice(0, 8)}</code>
              </div>
            </aside>
          </>
        )}
      </div>
    </main>
  );
}
