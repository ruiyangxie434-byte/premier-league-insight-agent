"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import type { CSSProperties } from "react";

import { getClubs, getStandings } from "../../services/api";
import type {
  ClubListData,
  StandingItem,
  StandingTableData,
} from "../../types/api";

type DataState = "loading" | "success" | "error";
type SortDirection = "asc" | "desc";
type SortKey =
  | "position"
  | "club"
  | "played"
  | "won"
  | "drawn"
  | "lost"
  | "goals_for"
  | "goals_against"
  | "goal_difference"
  | "points";

interface SortConfig {
  key: SortKey;
  direction: SortDirection;
}

const tableColumns: Array<{ key: SortKey; label: string }> = [
  { key: "position", label: "排名" },
  { key: "club", label: "球队" },
  { key: "played", label: "赛" },
  { key: "won", label: "胜" },
  { key: "drawn", label: "平" },
  { key: "lost", label: "负" },
  { key: "goals_for", label: "进球" },
  { key: "goals_against", label: "失球" },
  { key: "goal_difference", label: "净胜" },
  { key: "points", label: "积分" },
];

function getClubInitials(name: string) {
  return name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 3)
    .toUpperCase();
}

function getDefaultDirection(key: SortKey): SortDirection {
  return key === "position" || key === "club" ? "asc" : "desc";
}

function getSortValue(item: StandingItem, key: SortKey): number | string {
  if (key === "club") {
    return item.club.short_name;
  }
  return item[key];
}

function getLeagueZone(position: number) {
  if (position === 1) {
    return "champion";
  }
  if (position <= 5) {
    return "champions-league";
  }
  if (position >= 18) {
    return "relegated";
  }
  return "standard";
}

function formatSnapshotDate(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(new Date(`${value}T00:00:00`));
}

export function StageTwoData() {
  const [state, setState] = useState<DataState>("loading");
  const [clubs, setClubs] = useState<ClubListData | null>(null);
  const [standings, setStandings] = useState<StandingTableData | null>(null);
  const [selectedSlug, setSelectedSlug] = useState<string | null>(null);
  const [clubQuery, setClubQuery] = useState("");
  const [sortConfig, setSortConfig] = useState<SortConfig>({
    key: "position",
    direction: "asc",
  });
  const [requestId, setRequestId] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    async function loadData() {
      setState("loading");

      try {
        const [clubResponse, standingResponse] = await Promise.all([
          getClubs(controller.signal),
          getStandings("2024-25", controller.signal),
        ]);

        if (!clubResponse.data || !standingResponse.data) {
          throw new Error("接口未返回数据");
        }

        setClubs(clubResponse.data);
        setStandings(standingResponse.data);
        setSelectedSlug(
          (current) =>
            current ?? standingResponse.data?.items[0]?.club.slug ?? null,
        );
        setState("success");
      } catch {
        if (!controller.signal.aborted) {
          setState("error");
        }
      }
    }

    void loadData();
    return () => controller.abort();
  }, [requestId]);

  const selectedClub = useMemo(
    () => clubs?.items.find((club) => club.slug === selectedSlug) ?? null,
    [clubs, selectedSlug],
  );

  const filteredClubs = useMemo(() => {
    const query = clubQuery.trim().toLocaleLowerCase();
    if (!query) {
      return clubs?.items ?? [];
    }

    return (
      clubs?.items.filter((club) =>
        [club.name, club.short_name, club.city, club.stadium.name].some(
          (value) => value.toLocaleLowerCase().includes(query),
        ),
      ) ?? []
    );
  }, [clubQuery, clubs]);

  const sortedStandings = useMemo(() => {
    if (!standings) {
      return [];
    }

    return [...standings.items].sort((left, right) => {
      const leftValue = getSortValue(left, sortConfig.key);
      const rightValue = getSortValue(right, sortConfig.key);
      const comparison =
        typeof leftValue === "string" && typeof rightValue === "string"
          ? leftValue.localeCompare(rightValue, "en")
          : Number(leftValue) - Number(rightValue);

      if (comparison === 0) {
        return left.position - right.position;
      }
      return sortConfig.direction === "asc" ? comparison : -comparison;
    });
  }, [sortConfig, standings]);

  function handleSort(key: SortKey) {
    setSortConfig((current) => {
      if (current.key !== key) {
        return { key, direction: getDefaultDirection(key) };
      }
      return {
        key,
        direction: current.direction === "asc" ? "desc" : "asc",
      };
    });
  }

  function getAriaSort(key: SortKey) {
    if (sortConfig.key !== key) {
      return "none" as const;
    }
    return sortConfig.direction === "asc"
      ? ("ascending" as const)
      : ("descending" as const);
  }

  return (
    <section
      className="data-section"
      id="data-preview"
      aria-labelledby="data-title"
    >
      <div className="section-heading data-heading">
        <div>
          <p className="eyebrow">FULL LEAGUE SNAPSHOT</p>
          <h2 id="data-title">20 队积分与球场数据</h2>
        </div>
        <p>
          完整收录 2024-25 赛季 20 支球队及最终积分榜，并保留数据来源、快照日期和实时性边界。
        </p>
      </div>

      {state === "loading" && (
        <div className="data-loading" aria-live="polite">
          <span className="loading-ring" aria-hidden="true" />
          <div>
            <strong>正在读取完整联赛数据</strong>
            <p>同时请求 20 支球队与 2024-25 最终积分榜。</p>
          </div>
        </div>
      )}

      {state === "error" && (
        <div className="data-error" role="alert">
          <div>
            <span>DATA OFFLINE</span>
            <h3>暂时没有读到联赛数据</h3>
            <p>请确认后端终端仍在运行，然后点击重新连接。</p>
          </div>
          <button
            className="secondary-button"
            type="button"
            onClick={() => setRequestId((value) => value + 1)}
          >
            重新连接
          </button>
        </div>
      )}

      {state === "success" && clubs && standings && (
        <>
          <div className="data-metrics" aria-label="结构化数据概况">
            <div>
              <span>CLUBS</span>
              <strong>{clubs.total}</strong>
              <small>支赛季球队</small>
            </div>
            <div>
              <span>PLAYERS</span>
              <strong>{clubs.player_total}</strong>
              <small>条球员记录</small>
            </div>
            <div>
              <span>TABLE</span>
              <strong>{standings.total}</strong>
              <small>队完整终榜</small>
            </div>
            <div>
              <span>SEASON</span>
              <strong>{standings.season}</strong>
              <small>{formatSnapshotDate(standings.snapshot_date)} 快照</small>
            </div>
          </div>

          <div className="data-layout">
            <article className="clubs-panel">
              <div className="panel-title">
                <div>
                  <span>01</span>
                  <h3>球队数据索引</h3>
                </div>
                <small>{filteredClubs.length} / {clubs.total}</small>
              </div>

              <div className="club-search">
                <span aria-hidden="true">⌕</span>
                <input
                  aria-label="搜索球队、城市或球场"
                  onChange={(event) => setClubQuery(event.target.value)}
                  placeholder="搜索球队、城市或球场"
                  type="search"
                  value={clubQuery}
                />
              </div>

              <div className="club-list">
                {filteredClubs.map((club) => (
                  <button
                    className="club-card"
                    data-selected={club.slug === selectedSlug}
                    key={club.slug}
                    onClick={() => setSelectedSlug(club.slug)}
                    style={
                      {
                        "--club-color": club.primary_color,
                      } as CSSProperties
                    }
                    type="button"
                    aria-pressed={club.slug === selectedSlug}
                  >
                    <span className="club-monogram" aria-hidden="true">
                      {getClubInitials(club.short_name)}
                    </span>
                    <span className="club-card-copy">
                      <strong>{club.short_name}</strong>
                      <small>
                        {club.city} · {club.stadium.name}
                      </small>
                    </span>
                    <span className="club-arrow" aria-hidden="true">
                      ↗
                    </span>
                  </button>
                ))}

                {filteredClubs.length === 0 && (
                  <div className="club-search-empty">
                    没有匹配的球队，试试输入城市或球场名。
                  </div>
                )}
              </div>

              {selectedClub && (
                <div className="coordinate-readout" aria-live="polite">
                  <div>
                    <span>SELECTED GROUND</span>
                    <strong>{selectedClub.stadium.name}</strong>
                    <small>
                      {selectedClub.city} · 建队于{" "}
                      {selectedClub.founded_year ?? "未知"} 年
                    </small>
                  </div>
                  <div className="coordinate-actions">
                    <code>
                      {selectedClub.stadium.latitude.toFixed(4)},{" "}
                      {selectedClub.stadium.longitude.toFixed(4)}
                    </code>
                    <Link href={`/clubs/${selectedClub.slug}`}>
                      球队资料 ↗
                    </Link>
                  </div>
                </div>
              )}
            </article>

            <article className="standings-panel">
              <div className="panel-title">
                <div>
                  <span>02</span>
                  <h3>{standings.season} 最终积分榜</h3>
                </div>
                <small>点击表头排序</small>
              </div>

              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      {tableColumns.map((column) => (
                        <th
                          aria-sort={getAriaSort(column.key)}
                          key={column.key}
                          scope="col"
                        >
                          <button
                            className="table-sort-button"
                            data-active={sortConfig.key === column.key}
                            onClick={() => handleSort(column.key)}
                            type="button"
                          >
                            {column.label}
                            <span aria-hidden="true">
                              {sortConfig.key === column.key
                                ? sortConfig.direction === "asc"
                                  ? "↑"
                                  : "↓"
                                : "↕"}
                            </span>
                          </button>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {sortedStandings.map((item) => (
                      <tr
                        data-selected={item.club.slug === selectedSlug}
                        data-zone={getLeagueZone(item.position)}
                        key={item.club.slug}
                      >
                        <td className="rank-cell">{item.position}</td>
                        <td>
                          <button
                            className="table-club-button"
                            type="button"
                            onClick={() => setSelectedSlug(item.club.slug)}
                          >
                            <span
                              aria-hidden="true"
                              style={{ background: item.club.primary_color }}
                            />
                            {item.club.short_name}
                          </button>
                        </td>
                        <td>{item.played}</td>
                        <td>{item.won}</td>
                        <td>{item.drawn}</td>
                        <td>{item.lost}</td>
                        <td>{item.goals_for}</td>
                        <td>{item.goals_against}</td>
                        <td>
                          {item.goal_difference > 0 ? "+" : ""}
                          {item.goal_difference}
                        </td>
                        <td className="points-cell">{item.points}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="standing-legend" aria-label="积分榜标记说明">
                <span data-zone="champion"><i />冠军</span>
                <span data-zone="champions-league"><i />欧冠区（2–5）</span>
                <span data-zone="relegated"><i />降级</span>
                <small>颜色仅表示联赛名次区间，杯赛冠军资格另计。</small>
              </div>

              <p className="sample-notice">
                <span aria-hidden="true">i</span>
                <span>
                  {standings.sample_notice}{" "}
                  <a
                    href={standings.source_url}
                    rel="noreferrer"
                    target="_blank"
                  >
                    查看 {standings.source_name} ↗
                  </a>
                </span>
              </p>
            </article>
          </div>
        </>
      )}
    </section>
  );
}
