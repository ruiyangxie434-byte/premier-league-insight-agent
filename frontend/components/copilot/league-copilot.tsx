"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  getCopilotCapabilities,
  runCopilotQuery,
} from "../../services/api";
import type {
  CopilotAnswerData,
  CopilotCapabilitiesData,
  CopilotToolName,
} from "../../types/api";

const promptExamples = [
  "利物浦和阿森纳的最终排名、主客场表现和近五场状态有什么差异？",
  "萨卡和帕尔默谁更适合承担创造任务？",
  "2004 年 Arsenal 4–2 Liverpool 的射门和 xG 如何？",
  "2024-25 英超积分榜前三名是谁？",
];

const toolMeta: Record<CopilotToolName, { code: string; className: string }> = {
  get_league_table: { code: "TAB", className: "table" },
  get_club_form: { code: "FRM", className: "form" },
  compare_players: { code: "CMP", className: "compare" },
  get_match_shot_summary: { code: "xG", className: "match" },
};

function formatArgument(value: string | number | boolean | null) {
  if (value === null) {
    return "null";
  }
  if (typeof value === "boolean") {
    return value ? "true" : "false";
  }
  return String(value);
}

export function LeagueCopilot() {
  const [question, setQuestion] = useState(promptExamples[0]);
  const [capabilities, setCapabilities] =
    useState<CopilotCapabilitiesData | null>(null);
  const [result, setResult] = useState<CopilotAnswerData | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    getCopilotCapabilities(controller.signal)
      .then((response) => setCapabilities(response.data))
      .catch((requestError: unknown) => {
        if (requestError instanceof DOMException && requestError.name === "AbortError") {
          return;
        }
        setCapabilities(null);
      });
    return () => controller.abort();
  }, []);

  const modeLabel = useMemo(() => {
    if (!result) {
      return capabilities?.qwen_configured
        ? "QWEN TOOL CALLING"
        : "LOCAL TOOL ROUTER";
    }
    return result.generation.mode === "qwen_tool_calling"
      ? "QWEN TOOL CALLING"
      : "LOCAL TOOL ROUTER";
  }, [capabilities, result]);

  async function submitQuestion(activeQuestion: string) {
    const trimmed = activeQuestion.trim();
    if (trimmed.length < 6 || isRunning) {
      return;
    }
    setIsRunning(true);
    setError(null);
    try {
      const response = await runCopilotQuery({
        question: trimmed,
        season: "2024-25",
      });
      if (!response.data) {
        throw new Error("Copilot 没有返回可用结果");
      }
      setResult(response.data);
    } catch (requestError) {
      setResult(null);
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Copilot 请求失败，请稍后重试。",
      );
    } finally {
      setIsRunning(false);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void submitQuestion(question);
  }

  return (
    <>
      <section className="copilot-console" aria-labelledby="copilot-console-title">
        <div className="copilot-console-topline">
          <div>
            <p className="eyebrow">CONTROLLED FUNCTION CALLING</p>
            <h2 id="copilot-console-title">用一句话调度四类足球数据工具</h2>
          </div>
          <span
            className="copilot-mode-badge"
            data-mode={result?.generation.mode ?? capabilities?.default_mode}
          >
            <span aria-hidden="true" />
            {modeLabel}
          </span>
        </div>

        <div className="copilot-capability-grid" aria-label="Copilot 工具清单">
          {(capabilities?.tools ?? []).map((tool) => {
            const meta = toolMeta[tool.name];
            return (
              <article className="copilot-capability-card" key={tool.name}>
                <span className={`copilot-tool-code ${meta.className}`}>
                  {meta.code}
                </span>
                <div>
                  <strong>{tool.label}</strong>
                  <p>{tool.description}</p>
                  <small>{tool.data_scope}</small>
                </div>
              </article>
            );
          })}
          {!capabilities && (
            <p className="copilot-capability-loading">
              正在读取后端工具注册表…
            </p>
          )}
        </div>

        <form className="copilot-query-form" onSubmit={handleSubmit}>
          <label htmlFor="copilot-question">向 League Copilot 提问</label>
          <div className="copilot-prompt-list" aria-label="示例问题">
            {promptExamples.map((prompt) => (
              <button
                type="button"
                key={prompt}
                onClick={() => setQuestion(prompt)}
                data-active={question === prompt}
              >
                {prompt}
              </button>
            ))}
          </div>
          <textarea
            id="copilot-question"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            maxLength={500}
            rows={4}
            placeholder="例如：利物浦和阿森纳的最终排名、主客场表现和近五场状态有什么差异？"
          />
          <div className="copilot-form-footer">
            <p>
              {capabilities?.message ??
                "问题只会进入后端注册的受控工具，不进行无依据的自由问答。"}
            </p>
            <button
              className="copilot-run-button"
              type="submit"
              disabled={isRunning || question.trim().length < 6}
            >
              {isRunning ? (
                <>
                  <span className="loading-ring" aria-hidden="true" />
                  正在规划并执行工具
                </>
              ) : (
                <>
                  <span aria-hidden="true">▶</span>
                  运行 Copilot
                </>
              )}
            </button>
          </div>
        </form>

        {error && (
          <div className="copilot-error" role="alert">
            <strong>这次没有执行数据工具</strong>
            <p>{error}</p>
          </div>
        )}
      </section>

      {result && (
        <section className="copilot-result" aria-live="polite">
          <header className="copilot-answer-card">
            <div className="copilot-answer-meta">
              <span>{modeLabel}</span>
              <span>{result.tool_calls.length} 次工具调用</span>
              <span>{result.season}</span>
            </div>
            <p className="eyebrow">GROUNDED ANSWER</p>
            <h2>{result.headline}</h2>
            <p className="copilot-answer-copy">{result.answer}</p>
            <div className="copilot-answer-links">
              {result.links.map((link) => (
                <Link href={link.href} key={link.href}>
                  {link.label}
                  <span aria-hidden="true">↗</span>
                </Link>
              ))}
            </div>
            <p className="copilot-generation-note">{result.generation.note}</p>
          </header>

          <div className="copilot-result-layout">
            <section className="copilot-evidence-panel" aria-labelledby="copilot-evidence-title">
              <div className="copilot-panel-heading">
                <div>
                  <p className="eyebrow">VERIFIABLE EVIDENCE</p>
                  <h3 id="copilot-evidence-title">回答依据</h3>
                </div>
                <span>{result.evidence.length} 条</span>
              </div>
              <div className="copilot-evidence-grid">
                {result.evidence.map((item, index) => {
                  const meta = toolMeta[item.tool];
                  return (
                    <article key={`${item.tool}-${item.label}-${index}`}>
                      <div>
                        <span className={`copilot-tool-code compact ${meta.className}`}>
                          {meta.code}
                        </span>
                        <small>{item.label}</small>
                      </div>
                      <strong>{item.value}</strong>
                      <p>{item.detail}</p>
                    </article>
                  );
                })}
              </div>
            </section>

            <aside className="copilot-trace-panel" aria-labelledby="copilot-trace-title">
              <div className="copilot-panel-heading">
                <div>
                  <p className="eyebrow">EXECUTION TRACE</p>
                  <h3 id="copilot-trace-title">工具调用轨迹</h3>
                </div>
              </div>
              <ol className="copilot-trace-list">
                {result.tool_calls.map((call) => {
                  const meta = toolMeta[call.tool];
                  return (
                    <li key={call.call_id}>
                      <div className="copilot-trace-index">{call.index}</div>
                      <div className="copilot-trace-body">
                        <div className="copilot-trace-title-row">
                          <span className={`copilot-tool-code compact ${meta.className}`}>
                            {meta.code}
                          </span>
                          <strong>{call.label}</strong>
                          <span className="copilot-trace-status">完成</span>
                        </div>
                        <code>{call.tool}</code>
                        <dl>
                          {Object.entries(call.arguments).map(([key, value]) => (
                            <div key={key}>
                              <dt>{key}</dt>
                              <dd>{formatArgument(value)}</dd>
                            </div>
                          ))}
                        </dl>
                        <p>{call.summary}</p>
                        <a href={call.source.url} target="_blank" rel="noreferrer">
                          {call.source.name}
                          <span aria-hidden="true">↗</span>
                        </a>
                      </div>
                    </li>
                  );
                })}
              </ol>
            </aside>
          </div>

          <section className="copilot-boundary-card">
            <div>
              <p className="eyebrow">DATA BOUNDARY</p>
              <h3>Agent 知道自己不知道什么</h3>
              <p>{result.scope_notice}</p>
            </div>
            <ul>
              {result.limitations.map((limitation) => (
                <li key={limitation}>{limitation}</li>
              ))}
            </ul>
          </section>

          <section className="copilot-next-questions" aria-labelledby="copilot-next-title">
            <div>
              <p className="eyebrow">NEXT QUERY</p>
              <h3 id="copilot-next-title">继续验证另一条数据链</h3>
            </div>
            <div>
              {result.suggestions.map((suggestion) => (
                <button
                  type="button"
                  key={suggestion}
                  onClick={() => {
                    setQuestion(suggestion);
                    window.scrollTo({ top: 260, behavior: "smooth" });
                  }}
                >
                  {suggestion}
                  <span aria-hidden="true">→</span>
                </button>
              ))}
            </div>
          </section>
        </section>
      )}
    </>
  );
}
