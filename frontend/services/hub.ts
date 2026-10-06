import { getApiBaseUrl } from "./api";

export async function hubRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, { cache: "no-store", credentials: "include", ...options,
    headers: { Accept: "application/json", ...(options.body ? { "Content-Type": "application/json" } : {}), ...options.headers } });
  const body = await response.json();
  if (!response.ok) throw new Error(body.message ?? `请求失败：${response.status}`);
  return body.data as T;
}
export interface SeasonInfo { season: string; matches: number; played: number; fetched_at: string; source_url: string }
export interface Standing { team: string; rank: number; points: number; played: number; won: number; drawn: number; lost: number; goals_for: number; goals_against: number; goal_difference: number }
export interface ArchiveMatch { date: string; time?: string; round: string; team1: string; team2: string; score?: { ft?: number[] } }
export interface Archive { season: string; standings: Standing[]; matches: ArchiveMatch[]; source_url: string; fetched_at: string; notice: string }
export interface Forecast { home_win: number; draw: number; away_win: number; home_expected_goals: number; away_expected_goals: number; sample_matches: number; home_samples: number; away_samples: number; before: string; notice: string; scorelines: { score: string; probability: number }[] }
export interface Feed<T> { status: "ok" | "stale" | "unavailable" | "not_configured"; items: T[]; updated_at: string | null; source: string; message: string | null }
export interface NewsItem { title: string; url: string; published_at: string; source: string }
export interface ProviderTeam { id: number; name: string }
export interface Fixture { fixture: { id: number; date: string; status: { short: string; elapsed: number | null } }; teams: { home: ProviderTeam; away: ProviderTeam }; goals: { home: number | null; away: number | null } }
export interface Squad { team: ProviderTeam; players: { id: number; name: string; number: number | null; position: string; age: number | null }[] }
export interface Transfer { player: { id: number; name: string }; transfers: { date: string; type: string; teams: { in: ProviderTeam; out: ProviderTeam } }[] }
export interface Injury { player: { id: number; name: string; type: string; reason: string }; team: ProviderTeam; fixture: { id: number; date: string } }
export interface Lineup { team: ProviderTeam; formation: string | null; startXI: { player: { id: number; name: string; number: number | null; pos: string | null } }[]; substitutes: { player: { id: number; name: string; number: number | null } }[] }
