import Link from "next/link";

import { AnalysisAgent } from "../components/agent/analysis-agent";
import { StageTwoData } from "../components/data/stage-two-data";
import { EnglandClubMap } from "../components/map/england-club-map";
import { BackendStatus } from "../components/system/backend-status";

const futureModules = [
  {
    phase: "v0.12 已上线",
    title: "Player Intelligence Atlas",
    description: "574 条球员—球队记录、位置百分位、完整球队阵容与 Agent 球员覆盖已经打通。",
  },
  {
    phase: "数据下一步",
    title: "多赛季对照",
    description: "在保留数据许可、赛季边界和转会分段的前提下，扩展跨赛季变化分析。",
  },
  {
    phase: "v1.0 目标",
    title: "在线演示发布",
    description: "完成安全部署、最终回归测试和首个可公开访问版本。",
  },
];

export default function Home() {
  return (
    <main>
      <div className="page-shell">
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
          <span className="phase-badge">
            v0.12.0 · Player Intelligence Atlas
          </span>
        </header>

        <section className="hero" aria-labelledby="hero-title">
          <div className="hero-copy">
            <p className="eyebrow">
              Premier League · Geography · Data · Agent
            </p>
            <h1 id="hero-title">
              先从主场出发，
              <span>再让数据回答。</span>
            </h1>
            <p className="hero-description">
              在英格兰地图上探索球队与球场，再让英超智析 Agent
              调用受控数据工具，查询球员、赛季与比赛证据，再生成可核查的中文分析。
            </p>
            <div className="hero-actions">
              <a className="primary-button" href="#club-map">
                探索英格兰球场
              </a>
              <Link className="secondary-button" href="/players">
                打开球员实验室
              </Link>
              <Link className="secondary-button" href="/matches">
                打开比赛实验室
              </Link>
              <Link className="secondary-button" href="/form">
                打开赛季状态实验室
              </Link>
              <Link className="secondary-button" href="/copilot">
                体验 League Copilot
              </Link>
              <a className="secondary-button" href="#analysis-agent">
                体验分析 Agent
              </a>
            </div>
          </div>

          <BackendStatus />
        </section>

        <EnglandClubMap />

        <AnalysisAgent />

        <StageTwoData />

        <section className="module-section" id="roadmap" aria-labelledby="roadmap-title">
          <div className="section-heading">
            <div>
              <p className="eyebrow">BUILD ROADMAP</p>
              <h2 id="roadmap-title">接下来做什么</h2>
            </div>
            <p>地图、完整球员快照、赛季赛果、单场事件、分析记录与真实工具调用已经打通，下一步面向多赛季与 v1.0 发布。</p>
          </div>

          <div className="module-grid">
            {futureModules.map((module) => (
              <article className="module-card" key={module.phase}>
                <span>{module.phase}</span>
                <h3>{module.title}</h3>
                <p>{module.description}</p>
              </article>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
