"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { SiteHeader } from "../../components/system/site-header";
import { PlayerPortrait } from "../../components/players/player-portrait";
import { getClubs, getTransferSignals } from "../../services/api";
import type {
  ClubSummary,
  TransferPosition,
  TransferSignalData,
} from "../../types/api";

const positionOptions: Array<{ value: TransferPosition; label: string }> = [
  { value: "GK", label: "门将 · GK" },
  { value: "DEF", label: "后卫 · DEF" },
  { value: "MID", label: "中场 · MID" },
  { value: "FWD", label: "前锋 · FWD" },
];

const minuteOptions = [450, 900, 1800];
const validPositions = new Set<TransferPosition>(["GK", "DEF", "MID", "FWD"]);

function formatNumber(value: number) {
  return new Intl.NumberFormat("zh-CN").format(value);
}

export default function TransferPage() {
  const [clubs, setClubs] = useState<ClubSummary[]>([]);
  const [clubSlug, setClubSlug] = useState("liverpool");
  const [position, setPosition] = useState<TransferPosition>("MID");
  const [minimumMinutes, setMinimumMinutes] = useState(900);
  const [data, setData] = useState<TransferSignalData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    getClubs(controller.signal)
      .then((response) => {
        const items = response.data?.items ?? [];
        setClubs(items);
        const params = new URLSearchParams(window.location.search);
        const queryClub = params.get("club");
        const queryPosition = params.get("position") as TransferPosition | null;
        if (queryClub && items.some((club) => club.slug === queryClub)) {
          setClubSlug(queryClub);
        }
        if (queryPosition && validPositions.has(queryPosition)) {
          setPosition(queryPosition);
        }
      })
      .catch(() => undefined);
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    getTransferSignals(
      clubSlug,
      position,
      minimumMinutes,
      6,
      "2024-25",
      controller.signal,
    )
      .then((response) => {
        if (!response.data) throw new Error("候选信号为空");
        setData(response.data);
        setError(false);
      })
      .catch(() => {
        if (!controller.signal.aborted) setError(true);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [clubSlug, minimumMinutes, position]);

  const topScore = useMemo(
    () => data?.candidates[0]?.signal_score ?? 0,
    [data],
  );

  function updateQuery(nextClub: string, nextPosition: TransferPosition) {
    const search = new URLSearchParams({
      club: nextClub,
      position: nextPosition,
    });
    window.history.replaceState(null, "", `/transfer?${search.toString()}`);
  }

  function chooseClub(next: string) {
    setLoading(true);
    setError(false);
    setClubSlug(next);
    updateQuery(next, position);
  }

  function choosePosition(next: TransferPosition) {
    setLoading(true);
    setError(false);
    setPosition(next);
    updateQuery(clubSlug, next);
  }

  function chooseMinimumMinutes(next: number) {
    setLoading(true);
    setError(false);
    setMinimumMinutes(next);
  }

  return (
    <main className="transfer-page">
      <div className="page-shell transfer-shell">
        <SiteHeader />
        <Link className="club-back-link" href="/squad">
          <span aria-hidden="true">←</span>返回阵容透镜
        </Link>

        <section className="transfer-hero">
          <div>
            <p className="eyebrow">TRANSFER SIGNAL · EXPLAINABLE SHORTLIST</p>
            <h1>识别缺口，<span>解释候选。</span></h1>
            <p>
              用球队同位置百分位建立基线，再从外队历史记录中寻找正向统计信号。
              每个候选同时展示提升项、权衡项与样本置信度。
            </p>
          </div>
          <div className="transfer-hero-mark" aria-hidden="true">
            <span>DECISION SUPPORT</span>
            <strong>SIG</strong>
            <small>NEED · LIFT · TRADE-OFF</small>
          </div>
        </section>

        <section className="transfer-controls" aria-label="候选信号筛选">
          <label>
            <span>目标球队</span>
            <select value={clubSlug} onChange={(event) => chooseClub(event.target.value)}>
              {clubs.map((club) => (
                <option key={club.slug} value={club.slug}>{club.name}</option>
              ))}
            </select>
          </label>
          <label>
            <span>目标位置</span>
            <select
              value={position}
              onChange={(event) => choosePosition(event.target.value as TransferPosition)}
            >
              {positionOptions.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </label>
          <label>
            <span>样本门槛</span>
            <select
              value={minimumMinutes}
              onChange={(event) => chooseMinimumMinutes(Number(event.target.value))}
            >
              {minuteOptions.map((value) => (
                <option key={value} value={value}>{value}+ 分钟</option>
              ))}
            </select>
          </label>
          <div><span>计算状态</span><strong>{loading ? "正在重算" : "固定快照"}</strong></div>
        </section>

        {error && (
          <div className="match-page-state match-page-error" role="alert">
            <div><strong>候选信号读取失败</strong><p>请确认后端正在运行后重试。</p></div>
          </div>
        )}

        {data && (
          <div className={loading ? "transfer-content is-refreshing" : "transfer-content"}>
            <section className="transfer-club-heading" style={{ borderColor: data.club.primary_color }}>
              <div>
                <span>{data.season} · {data.position} SIGNAL</span>
                <h2>{data.club.name}</h2>
              </div>
              <p>
                {data.minimum_minutes}+ 分钟历史统计池
                <small>不是实时转会、身价或签约建议</small>
              </p>
            </section>

            {!data.is_supported ? (
              <section className="transfer-unavailable">
                <span>BOUNDARY STOP</span>
                <h2>不生成排名</h2>
                <p>{data.unavailable_reason}</p>
                <small>{data.decision_notice}</small>
              </section>
            ) : (
              <>
                <section className="transfer-kpis" aria-label="候选信号概览">
                  <article><span>球队位置记录</span><strong>{data.club_record_count}</strong><p>用于建立目标基线</p></article>
                  <article><span>同位置比较池</span><strong>{data.peer_record_count}</strong><p>{data.minimum_minutes}+ 分钟记录</p></article>
                  <article><span>有效候选</span><strong>{data.candidate_total}</strong><p>已排除目标球队与重复姓名</p></article>
                  <article><span>首位信号分</span><strong>{topScore}<small>/100</small></strong><p>不是成交概率</p></article>
                </section>

                <section className="transfer-section">
                  <div className="section-heading">
                    <div><p className="eyebrow">CLUB NEED PROFILE</p><h2>优先观察缺口</h2></div>
                    <p>优先级同时考虑位置权重与球队同位置基线；P50 代表比较池中位附近。</p>
                  </div>
                  <div className="transfer-needs">
                    {data.needs.map((need, index) => (
                      <article key={need.key}>
                        <header><span>0{index + 1}</span><small>优先级 {need.priority}</small></header>
                        <h3>{need.label}<small> / 90</small></h3>
                        <strong>P{need.club_percentile}</strong>
                        <div><i style={{ width: `${need.club_percentile}%` }} /></div>
                        <p>球队该位置平均百分位</p>
                      </article>
                    ))}
                  </div>
                </section>

                <section className="transfer-section">
                  <div className="section-heading">
                    <div><p className="eyebrow">EXPLAINABLE CANDIDATES</p><h2>历史统计候选</h2></div>
                    <p>只展示对至少一项优先缺口形成正向提升的外队球员记录。</p>
                  </div>
                  <div className="transfer-candidate-grid">
                    {data.candidates.map((candidate, index) => (
                      <article className="transfer-candidate" key={candidate.slug}>
                        <header>
                          <span>{String(index + 1).padStart(2, "0")}</span>
                          <div>
                            <strong>{candidate.signal_score}</strong>
                            <small>SIGNAL</small>
                          </div>
                        </header>
                        <Link className="transfer-candidate-player" href={`/players/${candidate.slug}`}>
                          <PlayerPortrait color={candidate.club.primary_color} name={candidate.full_name} size="md" slug={candidate.slug} />
                          <span>
                          {candidate.full_name}
                          <small>{candidate.club.short_name} · {candidate.nationality}</small>
                          </span>
                        </Link>
                        <dl>
                          <div><dt>分钟</dt><dd>{formatNumber(candidate.minutes)}</dd></div>
                          <div><dt>出场</dt><dd>{candidate.appearances}</dd></div>
                          <div><dt>置信度</dt><dd>{candidate.confidence_score}</dd></div>
                        </dl>
                        <div className="transfer-gap-list">
                          <span>正向提升</span>
                          {candidate.key_lifts.map((gap) => (
                            <p key={gap.key}><strong>{gap.label}</strong><i>+{gap.gap} PCT</i></p>
                          ))}
                        </div>
                        <div className="transfer-tradeoffs">
                          <span>权衡项</span>
                          <p>
                            {candidate.tradeoffs.length
                              ? candidate.tradeoffs.map((gap) => `${gap.label} ${gap.gap}`).join(" · ")
                              : "当前加权指标未低于球队基线"}
                          </p>
                        </div>
                      </article>
                    ))}
                  </div>
                </section>
              </>
            )}

            <section className="transfer-method">
              <div><p className="eyebrow">GROUNDING CONTRACT</p><h2>信号，不是答案。</h2></div>
              <div><p>{data.sample_notice}</p><p>{data.method_notice}</p><p>{data.decision_notice}</p></div>
              <footer>
                <span>{data.source_name} · v{data.source_version} · {data.license_name}</span>
                <a href={data.source_url} target="_blank" rel="noreferrer">查看原始数据源 →</a>
              </footer>
            </section>
          </div>
        )}
      </div>
    </main>
  );
}
