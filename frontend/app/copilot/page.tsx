import type { Metadata } from "next";
import Link from "next/link";

import { LeagueCopilot } from "../../components/copilot/league-copilot";

export const metadata: Metadata = {
  title: "League Copilot | Premier League Insight Agent",
  description: "用受控函数调用查询英超积分榜、球队状态、球员比较与单场射门证据。",
};

export default function CopilotPage() {
  return (
    <main>
      <div className="page-shell copilot-page-shell">
        <header className="site-header">
          <Link className="brand" href="/" aria-label="英超智析 Agent 首页">
            <span className="brand-mark" aria-hidden="true">
              AI
            </span>
            <span>
              <strong>英超智析 Agent</strong>
              <small>Premier League Insight Agent</small>
            </span>
          </Link>
          <span className="phase-badge">v0.12.0 · Player Intelligence Atlas</span>
        </header>

        <section className="copilot-hero" aria-labelledby="copilot-hero-title">
          <div>
            <p className="eyebrow">ASK · PLAN · CALL · VERIFY</p>
            <h1 id="copilot-hero-title">
              不让模型猜数据，
              <span>让它先调用工具。</span>
            </h1>
            <p>
              League Copilot 会把自然语言问题拆成受控函数调用，后端负责查询、计算和参数校验；
              千问只在已配置时参与工具选择与证据表达。
            </p>
          </div>
          <div className="copilot-hero-proof" aria-label="Copilot 约束摘要">
            <span>01</span>
            <strong>4 个受控工具</strong>
            <p>积分榜、球队状态、球员比较、单场射门。</p>
            <span>02</span>
            <strong>0 个实时猜测</strong>
            <p>超出历史快照范围的问题会明确拒绝。</p>
          </div>
        </section>

        <LeagueCopilot />

        <nav className="copilot-page-nav" aria-label="其他数据实验室">
          <Link href="/form">赛季状态实验室</Link>
          <Link href="/players">球员实验室</Link>
          <Link href="/matches">比赛实验室</Link>
          <Link href="/#analysis-agent">Agent Notebook</Link>
        </nav>
      </div>
    </main>
  );
}
