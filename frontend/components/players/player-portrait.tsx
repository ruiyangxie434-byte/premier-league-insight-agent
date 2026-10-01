"use client";

import Image from "next/image";
import { useState } from "react";
import type { CSSProperties } from "react";
import portraitCodes from "../../lib/player-portrait-codes.json";

type PortraitSize = "xs" | "sm" | "md" | "hero";

const sizeConfig: Record<PortraitSize, { width: number; height: number; sizes: string }> = {
  xs: { width: 36, height: 36, sizes: "36px" },
  sm: { width: 48, height: 48, sizes: "48px" },
  md: { width: 72, height: 72, sizes: "72px" },
  hero: { width: 240, height: 260, sizes: "(max-width: 700px) 42vw, 240px" },
};

function initials(name: string) {
  return name
    .split(/\s+/)
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

export function PlayerPortrait({
  slug,
  name,
  color,
  size = "sm",
  priority = false,
  className,
}: {
  slug: string;
  name: string;
  color?: string;
  size?: PortraitSize;
  priority?: boolean;
  className?: string;
}) {
  const code = (portraitCodes as Record<string, number>)[slug];
  const [failureState, setFailureState] = useState({ slug, level: 0 });
  const source = failureState.slug === slug ? failureState.level : 0;
  const config = sizeConfig[size];
  const sources = code
    ? [
        `https://resources.premierleague.com/premierleague/photos/players/250x250/p${code}.png`,
        `https://resources.premierleague.com/premierleague25/photos/players/110x140/${code}.png`,
      ]
    : [];
  const image = source < sources.length ? sources[source] : null;

  return (
    <span
      aria-label={name}
      className={["player-portrait", `player-portrait--${size}`, className].filter(Boolean).join(" ")}
      role="img"
      style={{ "--player-club-color": color ?? "#48e5a4" } as CSSProperties}
    >
      {image ? (
        <Image
          alt=""
          className="player-portrait-image"
          height={config.height}
          onError={() => setFailureState((current) => ({
            slug,
            level: Math.min(current.slug === slug ? current.level + 1 : 1, 2),
          }))}
          priority={priority}
          sizes={config.sizes}
          src={image}
          width={config.width}
        />
      ) : (
        <span aria-hidden="true" className="player-portrait-fallback">
          {initials(name)}
        </span>
      )}
    </span>
  );
}
