import Link from "next/link";

import { RELEASE_LABEL } from "../../lib/product";

export function SiteHeader({ className }: { className?: string }) {
  return (
    <header className={["site-header", className].filter(Boolean).join(" ")}>
      <Link className="brand" href="/" aria-label="英超智析 Agent 首页">
        <span className="brand-mark" aria-hidden="true">
          AI
        </span>
        <span>
          <strong>英超智析 Agent</strong>
          <small>Premier League Insight Agent</small>
        </span>
      </Link>
      <nav className="site-utility-nav" aria-label="项目工具">
        <Link href="/evidence">数据证据</Link>
        <span className="phase-badge">{RELEASE_LABEL}</span>
      </nav>
    </header>
  );
}
