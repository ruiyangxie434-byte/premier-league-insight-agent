"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import type { CSSProperties, FormEvent } from "react";

import {
  getAgentCapabilities,
  getAgentPlayers,
  getAgentRun,
  getAgentRuns,
  runAgentAnalysis,
  runAgentFollowUp,
} from "../../services/api";
import type {
  AgentAnalysisData,
  AgentCapabilitiesData,
  AgentPlayerOption,
  AgentRequestedFocus,
  AgentRunSummary,
} from "../../types/api";

const FOCUS_OPTIONS: {
  value: AgentRequestedFocus;
  label: string;
  description: string;
}[] = [
  {
    value: "auto",
    label: "自动识别",
    description: "根据任务描述选择指标权重",
  },
  {
    value: "balanced",
    label: "综合",
    description: "攻防指标均衡",
  },
  {
    value: "scoring",
    label: "终结",
    description: "进球、xG与射门",
  },
  {
    value: "creativity",
    label: "创造",
    description: "助攻与关键传球",
  },
  {
    value: "pressing",
    label: "逼抢",
    description: "抢断与拦截优先",
  },
];

function formatRunTime(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function AnalysisAgent() {
  const [players, setPlayers] = useState<AgentPlayerOption[]>([]);
  const [capabilities, setCapabilities] =
    useState<AgentCapabilitiesData | null>(null);
  const [firstSlug, setFirstSlug] = useState("bukayo-saka");
  const [secondSlug, setSecondSlug] = useState("cole-palmer");
  const [focus, setFocus] =
    useState<AgentRequestedFocus>("auto");
  const [question, setQuestion] = useState(
    "萨卡和帕尔默，谁更适合高位逼抢体系？请给出数据依据。",
  );
  const [isLoadingPlayers, setIsLoadingPlayers] = useState(true);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AgentAnalysisData | null>(null);
  const [runs, setRuns] = useState<AgentRunSummary[]>([]);
  const [isLoadingRuns, setIsLoadingRuns] = useState(true);
  const [openingRunId, setOpeningRunId] = useState<string | null>(null);
  const [followUpQuestion, setFollowUpQuestion] = useState("");
  const [isFollowingUp, setIsFollowingUp] = useState(false);
  const [followUpError, setFollowUpError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    async function loadAgentData() {
      try {
        const [playersResponse, capabilityResponse, runResponse] =
          await Promise.all([
            getAgentPlayers("2024-25", controller.signal),
            getAgentCapabilities(controller.signal),
            getAgentRuns(8, controller.signal),
          ]);
        if (!playersResponse.data) {
          throw new Error("接口未返回球员数据");
        }
        setPlayers(playersResponse.data.items);
        setCapabilities(capabilityResponse.data);
        setRuns(runResponse.data?.items ?? []);

        const search = new URLSearchParams(window.location.search);
        const playerA = search.get("playerA");
        const playerB = search.get("playerB");
        const available = new Map(
          playersResponse.data.items.map((player) => [player.slug, player]),
        );
        if (
          playerA &&
          playerB &&
          playerA !== playerB &&
          available.has(playerA) &&
          available.has(playerB)
        ) {
          setFirstSlug(playerA);
          setSecondSlug(playerB);
          setQuestion(
            `${available.get(playerA)?.full_name} 和 ${available.get(playerB)?.full_name}，谁的综合表现更适合球队？请给出数据依据。`,
          );
        }
      } catch {
        if (!controller.signal.aborted) {
          setError("没有读取到可分析球员，请确认后端仍在运行。");
        }
      } finally {
        if (!controller.signal.aborted) {
          setIsLoadingPlayers(false);
          setIsLoadingRuns(false);
        }
      }
    }

    void loadAgentData();
    return () => controller.abort();
  }, []);

  const playerMap = useMemo(
    () => new Map(players.map((player) => [player.slug, player])),
    [players],
  );

  async function refreshRunHistory() {
    try {
      const response = await getAgentRuns(8);
      setRuns(response.data?.items ?? []);
    } catch {
      // A completed analysis remains usable even if history refresh fails.
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (firstSlug === secondSlug) {
      setError("请选择两名不同的球员。");
      return;
    }

    setError(null);
    setIsRunning(true);
    try {
      const response = await runAgentAnalysis({
        question,
        player_slugs: [firstSlug, secondSlug],
        season: "2024-25",
        focus,
      });
      if (!response.data) {
        throw new Error("Agent 没有返回分析结果");
      }
      setResult(response.data);
      setFollowUpQuestion("");
      await refreshRunHistory();
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Agent 暂时无法完成分析，请稍后重试。",
      );
    } finally {
      setIsRunning(false);
    }
  }

  async function handleOpenRun(runId: string) {
    setOpeningRunId(runId);
    setError(null);
    try {
      const response = await getAgentRun(runId);
      if (!response.data) {
        throw new Error("没有读取到分析记录");
      }
      const restored = response.data.result;
      setResult(restored);
      setQuestion(restored.question);
      setFocus(restored.requested_focus);
      setFirstSlug(restored.players[0].slug);
      setSecondSlug(restored.players[1].slug);
      setFollowUpQuestion("");
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "暂时无法恢复这条分析记录。",
      );
    } finally {
      setOpeningRunId(null);
    }
  }

  async function handleFollowUp(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!result || followUpQuestion.trim().length < 6) {
      return;
    }
    setFollowUpError(null);
    setIsFollowingUp(true);
    try {
      const response = await runAgentFollowUp(result.run_id, {
        question: followUpQuestion.trim(),
        focus,
      });
      if (!response.data) {
        throw new Error("Agent 没有返回追问结果");
      }
      setResult(response.data);
      setQuestion(followUpQuestion.trim());
      setFollowUpQuestion("");
      await refreshRunHistory();
    } catch (requestError) {
      setFollowUpError(
        requestError instanceof Error
          ? requestError.message
          : "Agent 暂时无法完成追问。",
      );
    } finally {
      setIsFollowingUp(false);
    }
  }

  return (
    <section className="agent-section" id="analysis-agent" aria-labelledby="agent-title">
      <div className="section-heading agent-heading">
        <div>
          <p className="eyebrow">PITCHMIND · AGENT MVP</p>
          <h2 id="agent-title">足球分析与球探决策 Agent</h2>
        </div>
        <p>
          Agent 会保存每次分析、恢复历史上下文并支持连续追问；结论仍由数据库工具
          重新计算，可一键整理为带来源与边界的球探报告。
        </p>
      </div>

      <div className="agent-notebook" aria-label="最近分析记录">
        <div className="notebook-heading">
          <div>
            <span>AGENT NOTEBOOK</span>
            <strong>最近分析记录</strong>
          </div>
          <small>{isLoadingRuns ? "正在读取" : `${runs.length} 条最近记录`}</small>
        </div>
        <div className="notebook-run-list">
          {!isLoadingRuns && runs.length === 0 && (
            <p className="notebook-empty">完成第一条分析后，记录会出现在这里。</p>
          )}
          {runs.map((run) => (
            <button
              className="notebook-run"
              data-active={result?.run_id === run.run_id}
              disabled={openingRunId !== null}
              key={run.run_id}
              onClick={() => void handleOpenRun(run.run_id)}
              type="button"
            >
              <span>
                {run.follow_up_depth > 0
                  ? `FOLLOW-UP ${run.follow_up_depth}`
                  : "NEW ANALYSIS"}
              </span>
              <strong>
                {run.players[0].full_name} × {run.players[1].full_name}
              </strong>
              <p>{run.question}</p>
              <small>
                {run.focus_label} · {formatRunTime(run.created_at)}
              </small>
            </button>
          ))}
        </div>
      </div>

      <div className="agent-workspace">
        <form className="agent-console" onSubmit={handleSubmit}>
          <div className="console-header">
            <div>
              <span className="live-dot" aria-hidden="true" />
              <strong>新建分析任务</strong>
            </div>
            <span
              className="console-mode"
              data-qwen={capabilities?.qwen_configured ?? false}
            >
              {capabilities?.qwen_configured
                ? `${capabilities.model} · ONLINE`
                : "LOCAL SAFE MODE · v0.11"}
            </span>
          </div>

          <div className="console-body">
            <div className="field-group">
              <div className="field-label">
                <label htmlFor="first-player">选择分析对象</label>
                <span>2 PLAYERS</span>
              </div>
              <div className="player-select-grid">
                <div className="select-shell">
                  <small>球员 A</small>
                  <select
                    id="first-player"
                    value={firstSlug}
                    onChange={(event) => setFirstSlug(event.target.value)}
                    disabled={isLoadingPlayers || isRunning}
                  >
                    {players.map((player) => (
                      <option value={player.slug} key={player.slug}>
                        {player.full_name} · {player.club_name}
                      </option>
                    ))}
                  </select>
                </div>
                <span className="versus-mark" aria-hidden="true">
                  VS
                </span>
                <div className="select-shell">
                  <small>球员 B</small>
                  <select
                    id="second-player"
                    value={secondSlug}
                    onChange={(event) => setSecondSlug(event.target.value)}
                    disabled={isLoadingPlayers || isRunning}
                  >
                    {players.map((player) => (
                      <option value={player.slug} key={player.slug}>
                        {player.full_name} · {player.club_name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            <fieldset className="field-group focus-fieldset">
              <legend>分析重点</legend>
              <div className="focus-grid">
                {FOCUS_OPTIONS.map((option) => (
                  <label
                    className="focus-option"
                    data-selected={focus === option.value}
                    key={option.value}
                  >
                    <input
                      type="radio"
                      name="focus"
                      value={option.value}
                      checked={focus === option.value}
                      onChange={() => setFocus(option.value)}
                      disabled={isRunning}
                    />
                    <strong>{option.label}</strong>
                    <small>{option.description}</small>
                  </label>
                ))}
              </div>
            </fieldset>

            <div className="field-group">
              <div className="field-label">
                <label htmlFor="agent-question">任务描述</label>
                <span>{question.length}/500</span>
              </div>
              <textarea
                id="agent-question"
                value={question}
                maxLength={500}
                rows={4}
                onChange={(event) => setQuestion(event.target.value)}
                disabled={isRunning}
              />
            </div>

            {error && (
              <p className="agent-error" role="alert">
                {error}
              </p>
            )}

            <button
              className="agent-run-button"
              type="submit"
              disabled={isLoadingPlayers || isRunning || question.length < 6}
            >
              {isRunning ? (
                <>
                  <span className="loading-ring" aria-hidden="true" />
                  Agent 正在计算并组织回答
                </>
              ) : (
                <>
                  <span aria-hidden="true">▶</span>
                  启动 Agent 分析
                </>
              )}
            </button>
            <p className="console-notice">
              {capabilities?.qwen_configured
                ? "千问只负责组织回答；得分、指标与证据仍由本地数据库工具计算。"
                : "尚未配置千问 API Key，当前自动使用本地规则模式，所有分析功能仍可运行。"}
            </p>
          </div>
        </form>

        <div className="agent-output" aria-live="polite">
          {!result && (
            <div className="agent-empty">
              <div className="agent-orbit" aria-hidden="true">
                <span>PM</span>
              </div>
              <p className="eyebrow">WAITING FOR TASK</p>
              <h3>把一个足球问题交给 Agent</h3>
              <p>
                运行后，这里会展示任务规划、工具调用、对比指标、证据链和最终建议。
              </p>
              <ol>
                <li>理解分析意图</li>
                <li>读取数据库记录</li>
                <li>计算每90分钟指标</li>
                <li>生成可追溯证据</li>
                <li>千问增强或本地安全回退</li>
              </ol>
            </div>
          )}

          {result && (
            <div className="agent-result">
              <div className="result-topbar">
                <span>
                  <i aria-hidden="true" />
                  TASK COMPLETED
                </span>
                <code>{result.run_id}</code>
              </div>

              {result.context.inherited_scope && (
                <div className="memory-banner">
                  <span>CONTEXT RESTORED</span>
                  <p>{result.context.note}</p>
                  <code>{result.context.parent_run_id}</code>
                </div>
              )}

              <article className="recommendation-card">
                <div
                  className="generation-banner"
                  data-mode={result.generation.mode}
                >
                  <span>
                    {result.generation.mode === "qwen_enhanced"
                      ? "QWEN ENHANCED"
                      : "LOCAL RULE ENGINE"}
                  </span>
                  <small>
                    {result.generation.model ?? "NO EXTERNAL MODEL"}
                  </small>
                </div>
                <h3>{result.recommendation.headline}</h3>
                <p>{result.recommendation.summary}</p>
                <p className="generation-note">
                  {result.generation.note}
                </p>
                <div className="score-row">
                  {result.players.map((player) => (
                    <div key={player.slug}>
                      <span
                        className="player-color"
                        style={
                          {
                            "--result-player-color": player.club_color,
                          } as CSSProperties
                        }
                      />
                      <div>
                        <small>{player.full_name}</small>
                        <strong>
                          {result.recommendation.scores[player.slug]}
                        </strong>
                      </div>
                    </div>
                  ))}
                  <div className="confidence-chip">
                    <small>置信度</small>
                    <strong>
                      {Math.round(result.recommendation.confidence * 100)}%
                    </strong>
                  </div>
                </div>
                <div className="result-actions">
                  <Link href={`/reports/${result.run_id}`}>
                    打开球探报告
                  </Link>
                  <span>可打印或保存为 PDF</span>
                </div>
              </article>

              <div className="result-block">
                <div className="result-block-title">
                  <span>01</span>
                  <h4>Agent 执行轨迹</h4>
                </div>
                <div className="agent-trace">
                  {result.steps.map((step) => (
                    <div className="trace-step" key={step.index}>
                      <span>{step.index}</span>
                      <div>
                        <strong>{step.title}</strong>
                        <code>{step.tool}</code>
                        <p>{step.detail}</p>
                      </div>
                      <i aria-label="已完成">✓</i>
                    </div>
                  ))}
                </div>
              </div>

              <div className="result-block">
                <div className="result-block-title">
                  <span>02</span>
                  <h4>{result.focus_label}指标</h4>
                </div>
                <div className="metric-grid">
                  {result.metrics.map((metric) => (
                    <article className="metric-card" key={metric.key}>
                      <div>
                        <strong>{metric.label}</strong>
                        <small>权重 {Math.round(metric.weight * 100)}%</small>
                      </div>
                      {metric.values.map((value) => {
                        const player = playerMap.get(value.player_slug);
                        return (
                          <div className="metric-player" key={value.player_slug}>
                            <span>{player?.full_name ?? value.player_slug}</span>
                            <strong>{value.value.toFixed(2)}</strong>
                            <div
                              className="metric-bar"
                              title={`固定球员池百分位 ${value.percentile}`}
                            >
                              <i
                                style={{
                                  width: `${value.percentile}%`,
                                  background:
                                    player?.club_color ?? "var(--accent)",
                                }}
                              />
                            </div>
                            <small>P{value.percentile}</small>
                          </div>
                        );
                      })}
                    </article>
                  ))}
                </div>
              </div>

              <div className="result-block">
                <div className="result-block-title">
                  <span>03</span>
                  <h4>关键证据</h4>
                </div>
                <div className="evidence-list">
                  {result.evidence.map((item) => (
                    <article key={item.title}>
                      <strong>{item.title}</strong>
                      <p>{item.detail}</p>
                    </article>
                  ))}
                </div>
              </div>

              <form className="follow-up-panel" onSubmit={handleFollowUp}>
                <div>
                  <span>FOLLOW-UP</span>
                  <strong>基于这次分析继续追问</strong>
                  <p>沿用同一组球员与赛季，按上方分析重点重新计算。</p>
                </div>
                <textarea
                  aria-label="追问内容"
                  maxLength={500}
                  onChange={(event) => setFollowUpQuestion(event.target.value)}
                  placeholder="例如：如果更重视创造机会，结论会改变吗？"
                  rows={3}
                  value={followUpQuestion}
                  disabled={isFollowingUp}
                />
                {followUpError && (
                  <p className="agent-error" role="alert">
                    {followUpError}
                  </p>
                )}
                <button
                  type="submit"
                  disabled={isFollowingUp || followUpQuestion.trim().length < 6}
                >
                  {isFollowingUp ? "正在读取上下文并重新计算" : "提交追问"}
                </button>
              </form>

              <div className="limitations">
                <strong>结论边界</strong>
                <ul>
                  {result.limitations.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
                <p>{result.sample_notice}</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
