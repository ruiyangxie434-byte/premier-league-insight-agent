"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import type { CSSProperties } from "react";

import { getAgentRun } from "../../../services/api";
import type { AgentRunDetailData } from "../../../types/api";

type PageState = "loading" | "success" | "error";

function formatReportDate(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export default function AgentReportPage() {
  const params = useParams<{ runId: string }>();
  const [state, setState] = useState<PageState>("loading");
  const [data, setData] = useState<AgentRunDetailData | null>(null);
  const [requestId, setRequestId] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    async function loadReport() {
      setState("loading");
      try {
        const response = await getAgentRun(params.runId, controller.signal);
        if (!response.data) {
          throw new Error("报告数据为空");
        }
        setData(response.data);
        setState("success");
      } catch {
        if (!controller.signal.aborted) {
          setState("error");
        }
      }
    }

    void loadReport();
    return () => controller.abort();
  }, [params.runId, requestId]);

  return (
    <main className="report-page">
      <div className="page-shell report-shell">
        <header className="site-header report-site-header">
          <Link className="brand" href="/" aria-label="英超智析 Agent 首页">
            <span className="brand-mark" aria-hidden="true">AI</span>
            <span>
              <strong>英超智析 Agent</strong>
              <small>Premier League Insight Agent</small>
            </span>
          </Link>
          <span className="phase-badge">v0.11.0 · League Copilot</span>
        </header>

        <div className="report-toolbar">
          <Link href="/#analysis-agent">← 返回 Agent 工作台</Link>
          {state === "success" && (
            <button type="button" onClick={() => window.print()}>
              打印 / 保存 PDF
            </button>
          )}
        </div>

        {state === "loading" && (
          <div className="report-state" aria-live="polite">
            <span className="loading-ring" aria-hidden="true" />
            <div>
              <strong>正在整理球探报告</strong>
              <p>恢复指标、证据链、工具轨迹与结论边界。</p>
            </div>
          </div>
        )}

        {state === "error" && (
          <div className="report-state report-state-error" role="alert">
            <div>
              <strong>暂时无法打开这份报告</strong>
              <p>请确认后端仍在运行，且分析记录尚未被清除。</p>
            </div>
            <button type="button" onClick={() => setRequestId((value) => value + 1)}>
              重新读取
            </button>
          </div>
        )}

        {state === "success" && data && (
          <article className="scout-report">
            <header className="report-masthead">
              <div>
                <span>PLAYER COMPARISON · SCOUT REPORT</span>
                <h1>球员对比球探报告</h1>
                <p>{data.result.season} · {data.result.focus_label}</p>
              </div>
              <dl>
                <div>
                  <dt>报告编号</dt>
                  <dd>{data.run_id}</dd>
                </div>
                <div>
                  <dt>生成时间</dt>
                  <dd>{formatReportDate(data.created_at)}</dd>
                </div>
                <div>
                  <dt>生成模式</dt>
                  <dd>
                    {data.result.generation.mode === "qwen_enhanced"
                      ? "Qwen Enhanced"
                      : "Local Rule Engine"}
                  </dd>
                </div>
              </dl>
            </header>

            {data.parent_run_id && (
              <section className="report-memory">
                <span>FOLLOW-UP CONTEXT · DEPTH {data.follow_up_depth}</span>
                <strong>{data.result.context.note}</strong>
                <p>父记录：{data.parent_run_id}</p>
              </section>
            )}

            <section className="report-question">
              <span>ANALYSIS BRIEF</span>
              <h2>分析任务</h2>
              <p>“{data.result.question}”</p>
            </section>

            <section className="report-player-grid">
              {data.result.players.map((player) => (
                <article
                  key={player.slug}
                  style={
                    { "--report-player-color": player.club_color } as CSSProperties
                  }
                >
                  <span>{player.position} · {player.club_name}</span>
                  <h2>{player.full_name}</h2>
                  <p>{player.nationality} · {player.minutes.toLocaleString("en-US")} 分钟</p>
                  <strong>{data.result.recommendation.scores[player.slug]}</strong>
                  <small>AGENT SCORE / 100</small>
                </article>
              ))}
            </section>

            <section className="report-verdict">
              <div>
                <span>RECOMMENDATION</span>
                <small>
                  置信度 {Math.round(data.result.recommendation.confidence * 100)}%
                </small>
              </div>
              <h2>{data.result.recommendation.headline}</h2>
              <p>{data.result.recommendation.summary}</p>
              <small>{data.result.generation.note}</small>
            </section>

            <section className="report-section">
              <div className="report-section-heading">
                <span>01</span>
                <div>
                  <h2>指标对比</h2>
                  <p>所有累计数据已由后端换算为每 90 分钟，并在演示样例池内计算百分位。</p>
                </div>
              </div>
              <div className="report-table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>指标</th>
                      <th>权重</th>
                      {data.result.players.map((player) => (
                        <th key={player.slug}>{player.full_name}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {data.result.metrics.map((metric) => (
                      <tr key={metric.key}>
                        <th>{metric.label}<small>{metric.unit}</small></th>
                        <td>{Math.round(metric.weight * 100)}%</td>
                        {data.result.players.map((player) => {
                          const value = metric.values.find(
                            (item) => item.player_slug === player.slug,
                          );
                          return (
                            <td key={player.slug}>
                              <strong>{value?.value.toFixed(2) ?? "—"}</strong>
                              <small>P{value?.percentile ?? "—"}</small>
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="report-section">
              <div className="report-section-heading">
                <span>02</span>
                <div>
                  <h2>关键证据</h2>
                  <p>按百分位差距与本次任务权重排序，保留三条最能解释结论的证据。</p>
                </div>
              </div>
              <div className="report-evidence-grid">
                {data.result.evidence.map((evidence) => (
                  <article key={evidence.title}>
                    <strong>{evidence.title}</strong>
                    <p>{evidence.detail}</p>
                  </article>
                ))}
              </div>
            </section>

            <section className="report-section report-method">
              <div className="report-section-heading">
                <span>03</span>
                <div>
                  <h2>计算与生成轨迹</h2>
                  <p>每一步都保留工具名称，便于答辩时说明 Agent 如何得到结论。</p>
                </div>
              </div>
              <ol>
                {data.result.steps.map((step) => (
                  <li key={step.index}>
                    <span>{step.index}</span>
                    <div>
                      <strong>{step.title}</strong>
                      <code>{step.tool}</code>
                      <p>{step.detail}</p>
                    </div>
                  </li>
                ))}
              </ol>
            </section>

            <section className="report-boundaries">
              <div>
                <span>DATA SOURCE & BOUNDARIES</span>
                <h2>数据来源与结论边界</h2>
              </div>
              <p>{data.source_note}</p>
              <ul>
                {data.result.limitations.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
              <p>{data.result.sample_notice}</p>
              <a href={data.source_url} target="_blank" rel="noreferrer">
                {data.source_name} · 查看完整口径
              </a>
            </section>

            <footer className="report-footer">
              <strong>Premier League Insight Agent</strong>
              <span>{data.storage_notice}</span>
              <code>{data.run_id}</code>
            </footer>
          </article>
        )}
      </div>
    </main>
  );
}
