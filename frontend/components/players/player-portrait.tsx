"use client";

import Image from "next/image";
import { useEffect, useRef, useState } from "react";
import type { CSSProperties } from "react";
import portraitCodes from "../../lib/player-portrait-codes.json";

type PortraitSize = "xs" | "sm" | "md" | "hero";
const sizeConfig = {
  xs: { width: 36, height: 36, sizes: "36px" },
  sm: { width: 48, height: 48, sizes: "48px" },
  md: { width: 72, height: 72, sizes: "72px" },
  hero: { width: 240, height: 260, sizes: "(max-width: 700px) 42vw, 240px" },
};
function safeUrl(value: string) {
  return (value.startsWith("/") && !value.startsWith("//") && !value.includes("\\")) || /^https:\/\//i.test(value);
}

export function PlayerPortrait({ slug, name, color, size = "sm", priority = false, className, photoUrl, photoUrls = [] }: {
  slug: string; name: string; color?: string; size?: PortraitSize; priority?: boolean;
  className?: string; photoUrl?: string | null; photoUrls?: string[];
}) {
  const code = (portraitCodes as Record<string, number>)[slug];
  const sources = Array.from(new Set([
    ...(photoUrl ? [photoUrl] : []), ...photoUrls,
    ...(code ? [
      `https://resources.premierleague.com/premierleague/photos/players/250x250/p${code}.png`,
      `https://resources.premierleague.com/premierleague25/photos/players/110x140/${code}.png`,
    ] : []),
  ].filter(safeUrl)));
  const identity = JSON.stringify([slug, ...sources]);
  const [failure, setFailure] = useState({ identity, index: 0 });
  const index = failure.identity === identity ? failure.index : 0;
  const src = sources[index] ?? null;
  const element = useRef<HTMLSpanElement>(null);
  const loaded = useRef<string | null>(null);
  const config = sizeConfig[size];

  useEffect(() => {
    if (!src || !element.current) return;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const observer = new IntersectionObserver((entries) => {
      if (entries.some((entry) => entry.isIntersecting) && !timer) {
        timer = setTimeout(() => {
          if (loaded.current !== src) setFailure((current) => {
            const currentIndex = current.identity === identity ? current.index : 0;
            return currentIndex === index ? { identity, index: index + 1 } : current;
          });
        }, 12000);
      }
    });
    observer.observe(element.current);
    return () => { observer.disconnect(); if (timer) clearTimeout(timer); };
  }, [src, identity, index]);

  const letters = name.trim().split(/\s+/).map((part) => Array.from(part)[0] ?? "").join("").slice(0, 2).toUpperCase() || "?";
  return (
    <span ref={element} aria-label={`${name}${src ? "照片" : "（暂无照片）"}`} role="img"
      className={["player-portrait", `player-portrait--${size}`, className].filter(Boolean).join(" ")}
      style={{ "--player-club-color": color ?? "#48e5a4" } as CSSProperties}>
      {src ? <Image key={`${identity}:${index}`} src={src} alt="" width={config.width} height={config.height}
        className="player-portrait-image" priority={priority} sizes={config.sizes}
        // Custom API URLs load in the browser; Next cannot fetch arbitrary upstream hosts.
        unoptimized={!src.startsWith("https://resources.premierleague.com/") && !src.startsWith("/")}
        onLoad={() => { loaded.current = src; }}
        onError={() => setFailure((current) => {
          const currentIndex = current.identity === identity ? current.index : 0;
          return currentIndex === index ? { identity, index: index + 1 } : current;
        })} /> : <span aria-hidden="true" className="player-portrait-fallback">
          <svg viewBox="0 0 80 80" className="portrait-silhouette"><circle cx="40" cy="27" r="15"/><path d="M12 78v-9a28 28 0 0 1 56 0v9"/></svg>
          <span>{letters}</span>
        </span>}
    </span>
  );
}
