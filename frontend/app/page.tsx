import Link from "next/link";

import { AnalysisAgent } from "../components/agent/analysis-agent";
import { StageTwoData } from "../components/data/stage-two-data";
import { EnglandClubMap } from "../components/map/england-club-map";
import { BackendStatus } from "../components/system/backend-status";
import { SiteHeader } from "../components/system/site-header";

const futureModules = [
  {
    phase: "v0.18 已上线",
    title: "Club Briefing Room",
    description: "赛季、阵容与候选信号已汇成可打印、可核验的球队情报简报。",
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
        <SiteHeader />

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
              <Link className="secondary-button" href="/matchup">
                打开球队对阵实验室
              </Link>
              <Link className="secondary-button" href="/squad">
                打开阵容透镜
              </Link>
              <Link className="secondary-button" href="/transfer">
                打开候选信号
              </Link>
              <Link className="secondary-button" href="/briefing">
                生成球队情报简报
              </Link>
              <Link className="secondary-button" href="/copilot">
                体验 League Copilot
              </Link>
              <Link className="secondary-button" href="/evidence">
                核验数据证据
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
            <p>地图、球员分析、赛季赛果、单场事件、相似度、球队对阵、阵容透镜、候选信号、可打印球队简报、真实工具调用与统一证据目录已经打通，下一步面向 v1.0 发布。</p>
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
