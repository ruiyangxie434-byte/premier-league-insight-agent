"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import type { CSSProperties } from "react";

import { PlayerRadar } from "../../components/players/player-radar";
import { SiteHeader } from "../../components/system/site-header";
import { getPlayer, getPlayers } from "../../services/api";
import type {
  PlayerLabData,
  PlayerLabItem,
  PlayerPosition,
  PlayerSortKey,
  PlayerSortOrder,
} from "../../types/api";

type PageState = "loading" | "success" | "error";

const positionLabels: Record<PlayerPosition, string> = {
  FWD: "前锋",
  MID: "中场",
  DEF: "后卫",
  GK: "门将",
};

const columns: Array<{ key: PlayerSortKey; label: string }> = [
  { key: "full_name", label: "球员" },
  { key: "club", label: "球队" },
  { key: "position", label: "位置" },
  { key: "minutes", label: "分钟" },
  { key: "goals", label: "进球" },
  { key: "assists", label: "助攻" },
  { key: "goals_per90", label: "进球/90" },
  { key: "assists_per90", label: "助攻/90" },
  { key: "key_passes_per90", label: "关键传球/90" },
  { key: "tackles_per90", label: "抢断/90" },
];

function defaultDirection(key: PlayerSortKey): PlayerSortOrder {
  return key === "full_name" || key === "club" || key === "position"
    ? "asc"
    : "desc";
}

function initials(name: string) {
  return name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 3)
    .toUpperCase();
}

export default function PlayersPage() {
  const pageSize = 50;
  const [state, setState] = useState<PageState>("loading");
  const [data, setData] = useState<PlayerLabData | null>(null);
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [position, setPosition] = useState<PlayerPosition | "all">("all");
  const [clubSlug, setClubSlug] = useState("all");
  const [minimumMinutes, setMinimumMinutes] = useState(450);
  const [sortBy, setSortBy] = useState<PlayerSortKey>("goals_per90");
  const [order, setOrder] = useState<PlayerSortOrder>("desc");
  const [offset, setOffset] = useState(0);
  const [selectedPlayers, setSelectedPlayers] = useState<PlayerLabItem[]>([]);
  const [requestId, setRequestId] = useState(0);
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setDebouncedQuery(query);
      setOffset(0);
    }, 250);
    return () => window.clearTimeout(timer);
  }, [query]);

  useEffect(() => {
    const controller = new AbortController();
    async function loadPreferredComparison() {
      const requested = Array.from(
        new Set(
          new URLSearchParams(window.location.search)
            .get("compare")
            ?.split(",")
            .map((slug) => slug.trim())
            .filter(Boolean) ?? [],
        ),
      ).slice(0, 2);
      const defaults = ["bukayo-saka", "cole-palmer"];

      async function loadSlugs(slugs: string[]) {
        const responses = await Promise.all(
          slugs.map(async (slug) => {
            try {
              return await getPlayer(slug, "2024-25", controller.signal);
            } catch {
              return null;
            }
          }),
        );
        return responses
          .map((response) => response?.data ?? null)
          .filter((item): item is PlayerLabItem => Boolean(item));
      }

      let players = await loadSlugs(requested.length ? requested : defaults);
      if (!players.length && requested.length) {
        players = await loadSlugs(defaults);
      }
      if (!controller.signal.aborted) {
        setSelectedPlayers((current) => (current.length ? current : players));
      }
    }
    void loadPreferredComparison();
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    async function loadPlayers() {
      setState((current) => (current === "success" ? current : "loading"));
      setIsRefreshing(true);
      try {
        const response = await getPlayers(
          {
            minimumMinutes,
            query: debouncedQuery.trim() || undefined,
            position: position === "all" ? undefined : position,
            clubSlug: clubSlug === "all" ? undefined : clubSlug,
            limit: pageSize,
            offset,
            sortBy,
            order,
          },
          controller.signal,
        );
        if (!response.data) {
          throw new Error("球员数据为空");
        }
        setData(response.data);
        setState("success");
      } catch {
        if (!controller.signal.aborted) {
          setState("error");
        }
      } finally {
        if (!controller.signal.aborted) {
          setIsRefreshing(false);
        }
      }
    }

    void loadPlayers();
    return () => controller.abort();
  }, [clubSlug, debouncedQuery, minimumMinutes, offset, order, pageSize, position, requestId, sortBy]);

  const selectedSlugs = useMemo(
    () => selectedPlayers.map((player) => player.slug),
    [selectedPlayers],
  );

  function handleSort(key: PlayerSortKey) {
    if (sortBy === key) {
      setOrder((current) => (current === "asc" ? "desc" : "asc"));
      setOffset(0);
      return;
    }
    setSortBy(key);
    setOrder(defaultDirection(key));
    setOffset(0);
  }

  function togglePlayer(player: PlayerLabItem) {
    setSelectedPlayers((current) => {
      if (current.some((item) => item.slug === player.slug)) {
        return current.filter((item) => item.slug !== player.slug);
      }
      if (current.length >= 2) {
        return current;
      }
      return [...current, player];
    });
  }

  const agentHref =
    selectedPlayers.length === 2
      ? `/?playerA=${encodeURIComponent(selectedPlayers[0].slug)}&playerB=${encodeURIComponent(selectedPlayers[1].slug)}#analysis-agent`
      : "/#analysis-agent";

  return (
    <main>
      <div className="page-shell player-lab-shell">
        <SiteHeader />

        <Link className="club-back-link" href="/">
          <span aria-hidden="true">←</span>
          返回地图首页
        </Link>

        <section className="player-lab-hero" aria-labelledby="player-lab-title">
          <div>
            <p className="eyebrow">PLAYER INTELLIGENCE ATLAS · 2024/25</p>
            <h1 id="player-lab-title">
              从累计数据，
              <span>看到能力结构。</span>
            </h1>
            <p>
              浏览完整赛季球员—球队快照，由 FastAPI 统一换算每90分钟指标与同位置百分位；转会球员的两段俱乐部记录会分别保留。
            </p>
          </div>
          <div className="player-lab-hero-stats">
            <div>
              <span>RECORDS</span>
              <strong>{data?.dataset_total ?? "—"}</strong>
              <small>球员—球队记录</small>
            </div>
            <div>
              <span>PLAYERS</span>
              <strong>{data?.unique_player_total ?? "—"}</strong>
              <small>独立球员姓名</small>
            </div>
            <div>
              <span>QUALIFIED</span>
              <strong>{data?.pool_total ?? "—"}</strong>
              <small>{minimumMinutes ? `${minimumMinutes}+ 分钟` : "全部记录"}</small>
            </div>
          </div>
        </section>

        {state === "loading" && (
          <div className="player-lab-state" aria-live="polite">
            <span className="loading-ring" aria-hidden="true" />
            <div>
              <strong>正在构建球员数据中心</strong>
              <p>读取固定赛季快照、换算每90指标并计算位置百分位。</p>
            </div>
          </div>
        )}

        {state === "error" && (
          <div className="player-lab-state player-lab-error" role="alert">
            <div>
              <strong>暂时无法读取球员数据</strong>
              <p>请确认后端仍在运行，然后重新连接。</p>
            </div>
            <button
              className="secondary-button"
              onClick={() => setRequestId((value) => value + 1)}
              type="button"
            >
              重新连接
            </button>
          </div>
        )}

        {state === "success" && data && (
          <>
            <section
              aria-busy={isRefreshing}
              aria-labelledby="player-table-title"
              className="player-explorer"
              data-refreshing={isRefreshing}
            >
              <div className="player-explorer-heading">
                <div>
                  <p className="eyebrow">SORT · FILTER · INSPECT</p>
                  <h2 id="player-table-title">球员数据榜</h2>
                </div>
                <span>
                  {isRefreshing
                    ? "正在更新筛选结果…"
                    : `${data.total} 条匹配记录 · 当前显示 ${data.items.length} 条`}
                </span>
              </div>

              <div className="player-filter-bar">
                <label className="player-search-field">
                  <span>搜索</span>
                  <input
                    onChange={(event) => {
                      setQuery(event.target.value);
                    }}
                    placeholder="球员、球队或国籍"
                    type="search"
                    value={query}
                  />
                </label>
                <label>
                  <span>位置</span>
                  <select
                    onChange={(event) => {
                      setPosition(event.target.value as PlayerPosition | "all");
                      setOffset(0);
                    }}
                    value={position}
                  >
                    <option value="all">全部位置</option>
                    {data.available_positions.map((item) => (
                      <option key={item} value={item}>
                        {positionLabels[item]}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>球队</span>
                  <select
                    onChange={(event) => {
                      setClubSlug(event.target.value);
                      setOffset(0);
                    }}
                    value={clubSlug}
                  >
                    <option value="all">全部球队</option>
                    {data.available_clubs.map((club) => (
                      <option key={club.slug} value={club.slug}>
                        {club.short_name}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>最低分钟</span>
                  <select
                    onChange={(event) => {
                      setMinimumMinutes(Number(event.target.value));
                      setOffset(0);
                      setSelectedPlayers([]);
                    }}
                    value={minimumMinutes}
                  >
                    <option value={0}>全部出场记录</option>
                    <option value={450}>450 分钟（默认）</option>
                    <option value={1800}>1,800 分钟</option>
                    <option value={2700}>2,700 分钟</option>
                  </select>
                </label>
              </div>

              <div className="player-table-toolbar">
                <p>
                  选择球员加入右侧雷达比较
                  <strong>{selectedPlayers.length} / 2</strong>
                </p>
                <button
                  onClick={() => setSelectedPlayers([])}
                  type="button"
                >
                  清空选择
                </button>
              </div>

              <div className="player-table-scroll">
                <table className="player-table">
                  <thead>
                    <tr>
                      <th aria-label="选择球员" />
                      {columns.map((column) => (
                        <th
                          aria-sort={
                            sortBy === column.key
                              ? order === "asc"
                                ? "ascending"
                                : "descending"
                              : "none"
                          }
                          key={column.key}
                        >
                          <button
                            data-active={sortBy === column.key}
                            onClick={() => handleSort(column.key)}
                            type="button"
                          >
                            {column.label}
                            <span aria-hidden="true">
                              {sortBy === column.key
                                ? order === "asc"
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
                    {data.items.map((player) => {
                      const selected = selectedSlugs.includes(player.slug);
                      const selectionFull = selectedSlugs.length >= 2;
                      return (
                        <tr data-selected={selected} key={player.slug}>
                          <td>
                            <button
                              aria-label={`${selected ? "移除" : "选择"}${player.full_name}`}
                              className="player-select-button"
                              data-selected={selected}
                              disabled={!selected && selectionFull}
                              onClick={() => togglePlayer(player)}
                              type="button"
                            >
                              {selected ? "✓" : "+"}
                            </button>
                          </td>
                          <td>
                            <Link
                              className="player-name-cell"
                              href={`/players/${player.slug}`}
                            >
                              <span
                                style={
                                  {
                                    "--player-club-color":
                                      player.club.primary_color,
                                  } as CSSProperties
                                }
                              >
                                {initials(player.full_name)}
                              </span>
                              <strong>{player.full_name}</strong>
                            </Link>
                          </td>
                          <td>
                            <Link href={`/clubs/${player.club.slug}`}>
                              {player.club.short_name}
                            </Link>
                          </td>
                          <td>{positionLabels[player.position]}</td>
                          <td>{player.totals.minutes.toLocaleString("en-US")}</td>
                          <td>{player.totals.goals}</td>
                          <td>{player.totals.assists}</td>
                          <td>{player.per90.goals_per90.toFixed(2)}</td>
                          <td>{player.per90.assists_per90.toFixed(2)}</td>
                          <td>{player.per90.key_passes_per90.toFixed(2)}</td>
                          <td>{player.per90.tackles_per90.toFixed(2)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {data.items.length === 0 && (
                <div className="player-table-empty">
                  没有符合当前条件的球员，请降低分钟门槛或清除筛选。
                </div>
              )}

              {data.total > 0 && (
                <nav className="player-pagination" aria-label="球员数据分页">
                  <button
                    disabled={offset === 0}
                    onClick={() => setOffset(Math.max(0, offset - pageSize))}
                    type="button"
                  >
                    ← 上一页
                  </button>
                  <span>
                    {offset + 1}–{Math.min(offset + data.items.length, data.total)} / {data.total} 条
                  </span>
                  <button
                    disabled={offset + data.items.length >= data.total}
                    onClick={() => setOffset(offset + pageSize)}
                    type="button"
                  >
                    下一页 →
                  </button>
                </nav>
              )}

              <p className="player-data-notice">
                <span className="player-notice-icon" aria-hidden="true">i</span>
                <span className="player-notice-copy">
                  {data.sample_notice} 来源：
                  <a href={data.source_url} rel="noreferrer" target="_blank">
                    {data.source_name} v{data.source_version}
                  </a>
                  （
                  <a href={data.license_url} rel="noreferrer" target="_blank">
                    {data.license_name}
                  </a>
                  ）。
                </span>
              </p>
            </section>

            <section
              className="player-compare-section"
              id="player-radar"
              aria-labelledby="player-radar-title"
            >
              <div className="section-heading">
                <div>
                  <p className="eyebrow">POSITION-AWARE PERCENTILES</p>
                  <h2 id="player-radar-title">双球员能力雷达</h2>
                </div>
                <p>
                  数值表示球员在当前分钟门槛下对应位置池中的相对位置，不等同于实时排名或绝对能力评分。
                </p>
              </div>

              <div className="player-compare-layout">
                <article className="player-radar-panel">
                  <PlayerRadar players={selectedPlayers} />
                </article>

                <div className="player-compare-cards">
                  {selectedPlayers.map((player, index) => (
                    <article
                      key={player.slug}
                      style={
                        {
                          "--player-club-color": player.club.primary_color,
                        } as CSSProperties
                      }
                    >
                      <div className="compare-player-topline">
                        <span>PLAYER {index + 1}</span>
                        <button
                          onClick={() => togglePlayer(player)}
                          type="button"
                        >
                          移除
                        </button>
                      </div>
                      <div className="compare-player-identity">
                        <span>{initials(player.full_name)}</span>
                        <div>
                          <h3>{player.full_name}</h3>
                          <p>
                            {player.club.short_name} · {positionLabels[player.position]}
                          </p>
                        </div>
                      </div>
                      <div className="compare-player-metrics">
                        <div>
                          <span>进球/90</span>
                          <strong>{player.per90.goals_per90.toFixed(2)}</strong>
                        </div>
                        <div>
                          <span>助攻/90</span>
                          <strong>{player.per90.assists_per90.toFixed(2)}</strong>
                        </div>
                        <div>
                          <span>关键传球/90</span>
                          <strong>
                            {player.per90.key_passes_per90.toFixed(2)}
                          </strong>
                        </div>
                      </div>
                      <p className="percentile-scope">
                        {player.percentiles.scope === "position_pool"
                          ? `同位置 ${player.percentiles.peer_count} 条合格记录`
                          : `位置池不足，回退全部 ${player.percentiles.peer_count} 条记录`}
                      </p>
                      <Link href={`/players/${player.slug}`}>查看完整资料 →</Link>
                    </article>
                  ))}

                  {selectedPlayers.length < 2 && (
                    <div className="compare-slot-empty">
                      <span>{selectedPlayers.length + 1}</span>
                      <p>从上方球员榜再选择一名球员。</p>
                    </div>
                  )}
                </div>
              </div>

              <div className="player-compare-footer">
                <p>{data.percentile_notice}</p>
                <Link
                  className="primary-button"
                  href={agentHref}
                >
                  把这组对比交给 Agent
                </Link>
              </div>
            </section>
          </>
        )}
      </div>
    </main>
  );
}
