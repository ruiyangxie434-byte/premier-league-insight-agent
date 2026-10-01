"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { RELEASE_LABEL } from "../../lib/product";

export function SiteHeader({ className }: { className?: string }) {
  const pathname = usePathname();
  const navItems = [
    { href: "/players", label: "球员" },
    { href: "/#club-map", label: "球队地图" },
    { href: "/matches", label: "比赛" },
    { href: "/timeline", label: "赛季时间轴" },
    { href: "/squad", label: "阵容透镜" },
    { href: "/copilot", label: "AI 助手" },
  ];

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
      <nav className="site-utility-nav" aria-label="主要功能">
        {navItems.map((item) => (
          <Link
            aria-current={pathname === item.href ? "page" : undefined}
            href={item.href}
            key={item.href}
          >
            {item.label}
          </Link>
        ))}
        <span className="phase-badge">{RELEASE_LABEL}</span>
      </nav>
    </header>
  );
}
