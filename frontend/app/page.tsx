import Link from "next/link";

import { AnalysisAgent } from "../components/agent/analysis-agent";
import { StageTwoData } from "../components/data/stage-two-data";
import { EnglandClubMap } from "../components/map/england-club-map";
import { BackendStatus } from "../components/system/backend-status";

const futureModules = [
  {
    phase: "v0.10 已上线",
    title: "赛季状态实验室",
    description: "380 场完整赛果、38 轮积分走势、主客场拆分与球队末五场状态已经打通。",
  },
  {
    phase: "Agent 下一步",
    title: "真实函数调用",
    description: "让千问在受控工具清单中规划查询，同时继续保留本地安全降级。",
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
            v0.10.0 · Season Form Lab
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
              查询球员数据、换算每90分钟指标，并用完整赛季比分与真实比赛事件解释球队表现。
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
            <p>地图、球员、完整赛季、单场事件与可追问 Agent 报告链路已经打通，下一步面向真实工具调用与 v1.0 发布。</p>
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
