import type {
  AgentAnalysisData,
  AgentAnalysisRequest,
  AgentCapabilitiesData,
  AgentFollowUpRequest,
  AgentPlayerOptionData,
  AgentRunDetailData,
  AgentRunListData,
  ApiResponse,
  ClubDetailData,
  ClubMatchupData,
  ClubSeasonFormData,
  ClubListData,
  CopilotAnswerData,
  CopilotCapabilitiesData,
  CopilotQueryRequest,
  EvidenceCatalogData,
  HealthData,
  MatchDetailData,
  MatchListData,
  PlayerLabData,
  PlayerLabItem,
  PlayerLabQuery,
  PlayerSimilarityData,
  SeasonFormOverviewData,
  StandingTableData,
} from "../types/api";

const CONFIGURED_API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(
  /\/$/,
  "",
);

export function getApiBaseUrl(): string {
  if (CONFIGURED_API_BASE_URL) {
    return CONFIGURED_API_BASE_URL;
  }
  if (typeof window !== "undefined") {
    const hostname = ["localhost", "127.0.0.1"].includes(
      window.location.hostname,
    )
      ? window.location.hostname
      : "localhost";
    return `http://${hostname}:8000/api`;
  }
  return "http://localhost:8000/api";
}

export function getEvidenceCatalog(
  signal?: AbortSignal,
): Promise<ApiResponse<EvidenceCatalogData>> {
  return getApiData<EvidenceCatalogData>("/evidence", signal);
}

export async function getApiHealth(
  signal?: AbortSignal,
): Promise<ApiResponse<HealthData>> {
  const response = await fetch(`${getApiBaseUrl()}/health`, {
    method: "GET",
    headers: {
      Accept: "application/json",
    },
    cache: "no-store",
    signal,
  });

  if (!response.ok) {
    throw new Error(`健康检查失败：HTTP ${response.status}`);
  }

  return (await response.json()) as ApiResponse<HealthData>;
}

async function getApiData<T>(
  path: string,
  signal?: AbortSignal,
): Promise<ApiResponse<T>> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    method: "GET",
    headers: {
      Accept: "application/json",
    },
    cache: "no-store",
    signal,
  });

  if (!response.ok) {
    throw new Error(`数据请求失败：HTTP ${response.status}`);
  }

  return (await response.json()) as ApiResponse<T>;
}

export function getClubs(
  signal?: AbortSignal,
): Promise<ApiResponse<ClubListData>> {
  return getApiData<ClubListData>("/clubs", signal);
}

export function getClub(
  slug: string,
  signal?: AbortSignal,
): Promise<ApiResponse<ClubDetailData>> {
  return getApiData<ClubDetailData>(
    `/clubs/${encodeURIComponent(slug)}`,
    signal,
  );
}

export function getStandings(
  season = "2024-25",
  signal?: AbortSignal,
): Promise<ApiResponse<StandingTableData>> {
  return getApiData<StandingTableData>(
    `/standings?season=${encodeURIComponent(season)}`,
    signal,
  );
}

export function getMatches(
  signal?: AbortSignal,
): Promise<ApiResponse<MatchListData>> {
  return getApiData<MatchListData>("/matches", signal);
}

export function getMatch(
  sourceMatchId: string,
  signal?: AbortSignal,
): Promise<ApiResponse<MatchDetailData>> {
  return getApiData<MatchDetailData>(
    `/matches/${encodeURIComponent(sourceMatchId)}`,
    signal,
  );
}

export function getSeasonForm(
  season = "2024-25",
  signal?: AbortSignal,
): Promise<ApiResponse<SeasonFormOverviewData>> {
  return getApiData<SeasonFormOverviewData>(
    `/form?season=${encodeURIComponent(season)}`,
    signal,
  );
}

export function getClubSeasonForm(
  slug: string,
  season = "2024-25",
  signal?: AbortSignal,
): Promise<ApiResponse<ClubSeasonFormData>> {
  return getApiData<ClubSeasonFormData>(
    `/form/clubs/${encodeURIComponent(slug)}?season=${encodeURIComponent(season)}`,
    signal,
  );
}

export function getClubMatchup(
  clubA: string,
  clubB: string,
  season = "2024-25",
  signal?: AbortSignal,
): Promise<ApiResponse<ClubMatchupData>> {
  const search = new URLSearchParams({
    club_a: clubA,
    club_b: clubB,
    season,
  });
  return getApiData<ClubMatchupData>(`/form/matchup?${search.toString()}`, signal);
}

export function getPlayers(
  options: PlayerLabQuery = {},
  signal?: AbortSignal,
): Promise<ApiResponse<PlayerLabData>> {
  const search = new URLSearchParams({
    season: options.season ?? "2024-25",
    minimum_minutes: String(options.minimumMinutes ?? 450),
    sort_by: options.sortBy ?? "goals_per90",
    order: options.order ?? "desc",
    limit: String(options.limit ?? 50),
    offset: String(options.offset ?? 0),
  });
  if (options.query) {
    search.set("query", options.query);
  }
  if (options.position) {
    search.set("position", options.position);
  }
  if (options.clubSlug) {
    search.set("club_slug", options.clubSlug);
  }
  return getApiData<PlayerLabData>(`/players?${search.toString()}`, signal);
}

export function getPlayer(
  slug: string,
  season = "2024-25",
  signal?: AbortSignal,
): Promise<ApiResponse<PlayerLabItem>> {
  return getApiData<PlayerLabItem>(
    `/players/${encodeURIComponent(slug)}?season=${encodeURIComponent(season)}`,
    signal,
  );
}

export function getSimilarPlayers(
  slug: string,
  options: {
    season?: string;
    minimumMinutes?: number;
    limit?: number;
  } = {},
  signal?: AbortSignal,
): Promise<ApiResponse<PlayerSimilarityData>> {
  const search = new URLSearchParams({
    season: options.season ?? "2024-25",
    minimum_minutes: String(options.minimumMinutes ?? 450),
    limit: String(options.limit ?? 5),
  });
  return getApiData<PlayerSimilarityData>(
    `/players/${encodeURIComponent(slug)}/similar?${search.toString()}`,
    signal,
  );
}

export function getAgentPlayers(
  season = "2024-25",
  signal?: AbortSignal,
): Promise<ApiResponse<AgentPlayerOptionData>> {
  return getApiData<AgentPlayerOptionData>(
    `/agent/players?season=${encodeURIComponent(season)}`,
    signal,
  );
}

export function getAgentCapabilities(
  signal?: AbortSignal,
): Promise<ApiResponse<AgentCapabilitiesData>> {
  return getApiData<AgentCapabilitiesData>(
    "/agent/capabilities",
    signal,
  );
}

export async function runAgentAnalysis(
  payload: AgentAnalysisRequest,
  signal?: AbortSignal,
): Promise<ApiResponse<AgentAnalysisData>> {
  const response = await fetch(`${getApiBaseUrl()}/agent/analyze`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
    cache: "no-store",
    signal,
  });

  const body = (await response.json()) as ApiResponse<AgentAnalysisData>;
  if (!response.ok) {
    throw new Error(body.message || `Agent 请求失败：HTTP ${response.status}`);
  }
  return body;
}

export function getAgentRuns(
  limit = 8,
  signal?: AbortSignal,
): Promise<ApiResponse<AgentRunListData>> {
  return getApiData<AgentRunListData>(
    `/agent/runs?limit=${limit}&offset=0`,
    signal,
  );
}

export function getAgentRun(
  runId: string,
  signal?: AbortSignal,
): Promise<ApiResponse<AgentRunDetailData>> {
  return getApiData<AgentRunDetailData>(
    `/agent/runs/${encodeURIComponent(runId)}`,
    signal,
  );
}

export async function runAgentFollowUp(
  runId: string,
  payload: AgentFollowUpRequest,
  signal?: AbortSignal,
): Promise<ApiResponse<AgentAnalysisData>> {
  const response = await fetch(
    `${getApiBaseUrl()}/agent/runs/${encodeURIComponent(runId)}/follow-up`,
    {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
      cache: "no-store",
      signal,
    },
  );
  const body = (await response.json()) as ApiResponse<AgentAnalysisData>;
  if (!response.ok) {
    throw new Error(body.message || `追问失败：HTTP ${response.status}`);
  }
  return body;
}

export function getCopilotCapabilities(
  signal?: AbortSignal,
): Promise<ApiResponse<CopilotCapabilitiesData>> {
  return getApiData<CopilotCapabilitiesData>(
    "/copilot/capabilities",
    signal,
  );
}

export async function runCopilotQuery(
  payload: CopilotQueryRequest,
  signal?: AbortSignal,
): Promise<ApiResponse<CopilotAnswerData>> {
  const response = await fetch(`${getApiBaseUrl()}/copilot/query`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
    cache: "no-store",
    signal,
  });
  const body = (await response.json()) as ApiResponse<CopilotAnswerData>;
  if (!response.ok) {
    throw new Error(body.message || `Copilot 请求失败：HTTP ${response.status}`);
  }
  return body;
}
