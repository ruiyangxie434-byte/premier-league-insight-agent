import Link from "next/link";

import { AnalysisAgent } from "../components/agent/analysis-agent";
import { StageTwoData } from "../components/data/stage-two-data";
import { EnglandClubMap } from "../components/map/england-club-map";
import { PlayerPortrait } from "../components/players/player-portrait";
import { BackendStatus } from "../components/system/backend-status";
import { SiteHeader } from "../components/system/site-header";

const workspaces = [
  {
    number: "01",
    eyebrow: "PLAYER LAB",
    title: "球员观察",
    description: "从个人表现、雷达画像到球员对比，找到数据背后的特点。",
    href: "/players",
    action: "进入球员实验室",
    links: [{ label: "球员对比", href: "/players?compare=bukayo-saka,cole-palmer" }, { label: "相似球员", href: "/players" }],
  },
  {
    number: "02",
    eyebrow: "CLUB ROOM",
    title: "球队研究",
    description: "看主场位置、阵容构成、对阵表现与球队情报简报。",
    href: "#club-map",
    action: "浏览英格兰球队",
    links: [{ label: "阵容透镜", href: "/squad" }, { label: "球队对阵", href: "/matchup" }, { label: "情报简报", href: "/briefing" }],
  },
  {
    number: "03",
    eyebrow: "SEASON REVIEW",
    title: "赛季复盘",
    description: "沿着赛季时间轴回看积分变化、状态起伏与比赛结果。",
    href: "/timeline",
    action: "打开赛季时间轴",
    links: [{ label: "比赛记录", href: "/matches" }, { label: "近期状态", href: "/form" }, { label: "候选信号", href: "/transfer" }],
  },
  {
    number: "04",
    eyebrow: "AI WORKBENCH",
    title: "AI 分析工作台",
    description: "用自然语言提问，让 Agent 调用工具并给出可核查的证据。",
    href: "#analysis-agent",
    action: "体验分析 Agent",
    links: [{ label: "League Copilot", href: "/copilot" }, { label: "数据来源", href: "/evidence" }],
  },
];

export default function Home() {
  return (
    <main>
      <div className="page-shell home-shell">
        <SiteHeader />

        <section className="home-hero" aria-labelledby="hero-title">
          <div className="home-hero-copy">
            <p className="eyebrow">THE 2024—25 PREMIER LEAGUE, THROUGH DATA</p>
            <h1 id="hero-title">
              看见球员，
              <span>读懂比赛。</span>
            </h1>
            <p className="home-hero-description">
              从每一位球员的赛季表现出发，把英超地图、球队、比赛与数据证据连成一条清晰的探索路径。
            </p>
            <div className="home-hero-actions">
              <Link className="primary-button" href="/players">认识球员</Link>
              <a className="secondary-button" href="#workspace-grid">浏览全部功能 <span aria-hidden="true">↓</span></a>
            </div>
            <div className="home-season-facts" aria-label="数据范围">
              <div><strong>20</strong><span>支英超球队</span></div>
              <div><strong>562</strong><span>位球员</span></div>
              <div><strong>380</strong><span>场联赛比赛</span></div>
              <small>2024—25 赛季数据</small>
            </div>
          </div>

          <div className="home-hero-art" aria-label="英超球员照片">
            <div className="home-hero-orbit" aria-hidden="true" />
            <div className="home-player home-player--left">
              <PlayerPortrait slug="bukayo-saka" name="Bukayo Saka" color="#ef0107" size="hero" priority />
              <span>BUKAYO SAKA <small>ARSENAL</small></span>
            </div>
            <div className="home-player home-player--center">
              <PlayerPortrait slug="erling-haaland" name="Erling Haaland" color="#6caddf" size="hero" priority />
              <span>ERLING HAALAND <small>MANCHESTER CITY</small></span>
            </div>
            <div className="home-player home-player--right">
              <PlayerPortrait slug="mohamed-salah" name="Mohamed Salah" color="#c8102e" size="hero" priority />
              <span>MOHAMED SALAH <small>LIVERPOOL</small></span>
            </div>
            <div className="home-hero-stamp"><span>PL</span><small>DATA<br />SEASON<br />24 / 25</small></div>
          </div>
        </section>

        <section className="workspace-section" id="workspace-grid" aria-labelledby="workspace-title">
          <div className="workspace-heading">
            <div>
              <p className="eyebrow">YOUR PREMIER LEAGUE WORKSPACE</p>
              <h2 id="workspace-title">想看什么，从这里开始</h2>
            </div>
            <p>四个方向，一眼找到下一步。</p>
          </div>
          <div className="workspace-grid">
            {workspaces.map((workspace) => (
              <article className="workspace-card" key={workspace.number}>
                <div className="workspace-card-top"><span>{workspace.eyebrow}</span><span>{workspace.number}</span></div>
                <h3>{workspace.title}</h3>
                <p>{workspace.description}</p>
                <Link className="workspace-card-action" href={workspace.href}>{workspace.action}<span aria-hidden="true">↗</span></Link>
                <div className="workspace-card-links">
                  {workspace.links.map((item) => <Link href={item.href} key={item.label}>{item.label}</Link>)}
                </div>
              </article>
            ))}
          </div>
        </section>

        <EnglandClubMap />
        <AnalysisAgent />
        <StageTwoData />

        <footer className="home-footer">
          <div><strong>英超智析 Agent</strong><span>历史赛季数据 · 可追溯来源 · 2024—25</span></div>
          <details className="home-system-details">
            <summary>连接与版本</summary>
            <BackendStatus />
          </details>
          <Link href="/evidence">查看数据来源 <span aria-hidden="true">↗</span></Link>
        </footer>
      </div>
    </main>
  );
}
