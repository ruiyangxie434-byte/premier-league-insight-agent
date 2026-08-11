"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import type { CSSProperties } from "react";

import { getClub, getClubSeasonForm } from "../../../services/api";
import type {
  ClubDetailData,
  ClubSeasonFormData,
} from "../../../types/api";

type ClubPageState = "loading" | "success" | "error";

const positionLabels: Record<string, string> = {
  FWD: "前锋",
  MID: "中场",
  DEF: "后卫",
  GK: "门将",
};

function getClubInitials(name: string) {
  return name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 3)
    .toUpperCase();
}

function formatMatchDate(value: string | null) {
  if (!value) {
    return "日期待确认";
  }
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date(value));
}

export default function ClubDetailPage() {
  const params = useParams<{ slug: string }>();
  const [state, setState] = useState<ClubPageState>("loading");
  const [club, setClub] = useState<ClubDetailData | null>(null);
  const [clubForm, setClubForm] = useState<ClubSeasonFormData | null>(null);
  const [requestId, setRequestId] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    async function loadClub() {
      setState("loading");

      try {
        const [clubResponse, formResponse] = await Promise.all([
          getClub(params.slug, controller.signal),
          getClubSeasonForm(params.slug, "2024-25", controller.signal),
        ]);
        if (!clubResponse.data || !formResponse.data) {
          throw new Error("球队详情为空");
        }

        setClub(clubResponse.data);
        setClubForm(formResponse.data);
        setState("success");
      } catch {
        if (!controller.signal.aborted) {
          setState("error");
        }
      }
    }

    void loadClub();
    return () => controller.abort();
  }, [params.slug, requestId]);

  return (
    <main>
      <div className="page-shell club-detail-shell">
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
          <span className="phase-badge">v0.12.0 · Player Intelligence Atlas</span>
        </header>

        <Link className="club-back-link" href="/#club-map">
          <span aria-hidden="true">←</span>
          返回英格兰地图
        </Link>

        {state === "loading" && (
          <div className="club-page-state" aria-live="polite">
            <span className="loading-ring" aria-hidden="true" />
            <div>
              <strong>正在读取球队资料</strong>
              <p>从 FastAPI 获取球场、赛季状态与完整历史阵容快照。</p>
            </div>
          </div>
        )}

        {state === "error" && (
          <div className="club-page-state club-page-error" role="alert">
            <div>
              <span>CLUB DATA OFFLINE</span>
              <strong>暂时无法打开球队资料</strong>
              <p>请确认后端仍在运行，或返回地图选择其他球队。</p>
            </div>
            <button
              className="secondary-button"
              type="button"
              onClick={() => setRequestId((value) => value + 1)}
            >
              重新读取
            </button>
          </div>
        )}

        {state === "success" && club && clubForm && (
          <div
            className="club-detail-content"
            style={
              {
                "--club-color": club.primary_color,
              } as CSSProperties
            }
          >
            <section className="club-profile-hero">
              <div className="club-profile-monogram" aria-hidden="true">
                {getClubInitials(club.short_name)}
              </div>
              <div className="club-profile-copy">
                <p className="eyebrow">CLUB PROFILE · 2024/25 REFERENCE</p>
                <h1>{club.name}</h1>
                <p>
                  {club.city} · {club.stadium.name}
                </p>
              </div>

              <dl className="club-profile-facts">
                <div>
                  <dt>FOUNDED</dt>
                  <dd>{club.founded_year ?? "未知"}</dd>
                </div>
                <div>
                  <dt>PLAYERS</dt>
                  <dd>{club.players.length}</dd>
                </div>
                <div>
                  <dt>COORDINATES</dt>
                  <dd>
                    {club.stadium.latitude.toFixed(3)},{" "}
                    {club.stadium.longitude.toFixed(3)}
                  </dd>
                </div>
              </dl>
            </section>

            <section className="club-form-section" aria-labelledby="club-form-title">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">2024/25 SEASON FORM</p>
                  <h2 id="club-form-title">赛季是怎样走完的</h2>
                </div>
                <p>{clubForm.season} 已完赛快照 · 截止 {clubForm.snapshot_date}</p>
              </div>

              <div className="club-form-summary">
                <article>
                  <span>FINAL POSITION</span>
                  <strong>{clubForm.final_position}<small> / 20</small></strong>
                  <p>{clubForm.overall.points} 分 · {clubForm.overall.points_per_game} PPG</p>
                </article>
                <article>
                  <span>RECORD</span>
                  <strong>{clubForm.overall.won}<small> 胜</small></strong>
                  <p>{clubForm.overall.drawn} 平 · {clubForm.overall.lost} 负</p>
                </article>
                <article>
                  <span>GOAL BALANCE</span>
                  <strong>{clubForm.overall.goal_difference > 0 ? "+" : ""}{clubForm.overall.goal_difference}</strong>
                  <p>{clubForm.overall.goals_for} 进 · {clubForm.overall.goals_against} 失</p>
                </article>
                <article>
                  <span>UNBEATEN RUN</span>
                  <strong>{clubForm.longest_unbeaten}<small> 场</small></strong>
                  <p>赛季最长连续不败</p>
                </article>
              </div>

              <div className="club-form-detail-grid">
                <div className="club-form-splits">
                  <article>
                    <span>HOME · 主场</span>
                    <strong>{clubForm.home.points} 分</strong>
                    <p>{clubForm.home.won}胜 {clubForm.home.drawn}平 {clubForm.home.lost}负 · {clubForm.home.goals_for}:{clubForm.home.goals_against}</p>
                  </article>
                  <article>
                    <span>AWAY · 客场</span>
                    <strong>{clubForm.away.points} 分</strong>
                    <p>{clubForm.away.won}胜 {clubForm.away.drawn}平 {clubForm.away.lost}负 · {clubForm.away.goals_for}:{clubForm.away.goals_against}</p>
                  </article>
                </div>

                <div className="club-recent-results">
                  <div>
                    <span>LAST FIVE · 末五场</span>
                    <div className="form-chip-row">
                      {clubForm.recent_form.map((result, index) => (
                        <i data-result={result} key={`${result}-${index}`}>{result}</i>
                      ))}
                    </div>
                  </div>
                  <ol>
                    {clubForm.matches.slice(-5).reverse().map((match) => (
                      <li key={match.source_match_id}>
                        <i data-result={match.result}>{match.result}</i>
                        <span>
                          <small>MW {match.matchweek} · {match.is_home ? "主" : "客"}</small>
                          <strong>{match.opponent.short_name}</strong>
                        </span>
                        <b>{match.home_score}–{match.away_score}</b>
                        <time dateTime={match.kickoff_at ?? undefined}>{formatMatchDate(match.kickoff_at)}</time>
                      </li>
                    ))}
                  </ol>
                </div>
              </div>

              <div className="club-form-footer">
                <p>{clubForm.sample_notice}</p>
                <Link className="primary-button" href="/form">打开赛季状态实验室</Link>
              </div>
            </section>

            <section
              className="club-squad-section"
              aria-labelledby="club-squad-title"
            >
              <div className="section-heading">
                <div>
                  <p className="eyebrow">PLAYER SNAPSHOT · 2024/25</p>
                  <h2 id="club-squad-title">赛季出场记录</h2>
                </div>
                <p>
                  来自 Kaggle v1 的固定赛季快照；转会球员在不同俱乐部的记录分别展示，不代表当前实时名单。
                </p>
              </div>

              {club.players.length > 0 ? (
                <div className="club-player-grid">
                  {club.players.map((player) => (
                    <Link
                      className="club-player-card"
                      href={`/players/${player.slug}`}
                      key={player.slug}
                    >
                      <span className="player-shirt-number">
                        {player.shirt_number ?? "—"}
                      </span>
                      <div>
                        <small>
                          {positionLabels[player.position] ?? player.position}
                        </small>
                        <h3>{player.full_name}</h3>
                        <p>{player.nationality}</p>
                      </div>
                      <i aria-hidden="true" />
                    </Link>
                  ))}
                </div>
              ) : (
                <div className="club-squad-empty">
                  <span aria-hidden="true">20</span>
                  <div>
                    <strong>球队入口已经就位</strong>
                    <p>
                      这支球队的球场与基础资料已接入，但当前快照没有对应球员记录。
                    </p>
                  </div>
                </div>
              )}

              {club.featured_matches.length > 0 && (
                <div className="club-match-preview">
                  <div>
                    <span>OPEN EVENT SNAPSHOT</span>
                    <strong>这支球队有一场可分析比赛</strong>
                    <p>从球队资料继续进入射门位置、xG 对比和进球时间线。</p>
                  </div>
                  {club.featured_matches.map((match) => (
                    <Link
                      href={`/matches/${match.source_match_id}`}
                      key={match.source_match_id}
                    >
                      <small>{match.season} · {formatMatchDate(match.kickoff_at)}</small>
                      <strong>
                        {match.home_club_name} {match.home_score}–{match.away_score} {match.away_club_name}
                      </strong>
                      <span>{match.venue} · 打开比赛分析 →</span>
                    </Link>
                  ))}
                </div>
              )}

              <div className="club-detail-actions">
                <Link className="primary-button" href="/players">
                  打开球员实验室
                </Link>
                <Link className="secondary-button" href="/#analysis-agent">
                  用 Agent 比较球员
                </Link>
                <Link className="secondary-button" href="/#data-preview">
                  查看完整积分榜
                </Link>
                <Link className="secondary-button" href="/matches">
                  打开比赛实验室
                </Link>
                <Link className="secondary-button" href="/form">
                  查看赛季走势
                </Link>
              </div>
            </section>
          </div>
        )}
      </div>
    </main>
  );
}
