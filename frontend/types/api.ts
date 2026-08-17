export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T | null;
}

export interface HealthData {
  service: string;
  status: "healthy";
  environment: string;
  version: string;
}

export interface EvidenceSourceData {
  id: string;
  name: string;
  provider: string;
  source_url: string;
  license: string;
  coverage: string;
  snapshot_date: string;
  record_count: number;
  record_label: string;
  powers: string[];
  limitations: string[];
  status: "ready" | "limited";
}

export interface EvidenceCatalogData {
  generated_at: string;
  season_focus: string;
  sources: EvidenceSourceData[];
  source_count: number;
  ready_count: number;
  total_records: number;
  methodology: string[];
}

export interface StadiumData {
  name: string;
  latitude: number;
  longitude: number;
}

export interface ClubSummary {
  id: number;
  name: string;
  short_name: string;
  slug: string;
  city: string;
  stadium: StadiumData;
  founded_year: number | null;
  primary_color: string;
  source_kind: "reference" | "sample";
}

export interface ClubListData {
  items: ClubSummary[];
  total: number;
  player_total: number;
  limit: number;
  offset: number;
  season: string;
  is_complete: boolean;
  source_name: string;
  source_url: string;
  sample_notice: string;
}

export interface ClubPlayerSummary {
  id: number;
  full_name: string;
  slug: string;
  shirt_number: number | null;
  position: string;
  nationality: string;
  date_of_birth: string | null;
  birth_year: number | null;
  source_kind: "kaggle-fbref";
}

export interface ClubDetailData extends ClubSummary {
  players: ClubPlayerSummary[];
  featured_matches: ClubMatchPreview[];
}

export type SquadPosition = "GK" | "DEF" | "MID" | "FWD";
export type SquadLeaderMetric =
  | "minutes"
  | "goals"
  | "assists"
  | "key_passes"
  | "defensive_actions";

export interface SquadClubData {
  id: number;
  name: string;
  short_name: string;
  slug: string;
  primary_color: string;
}

export interface SquadPlayerData {
  full_name: string;
  slug: string;
  position: SquadPosition;
  nationality: string;
  appearances: number;
  starts: number;
  minutes: number;
  goals: number;
  assists: number;
  minutes_share: number;
}

export interface SquadPositionGroup {
  position: SquadPosition;
  label: string;
  record_count: number;
  minutes: number;
  minutes_share: number;
  goals: number;
  assists: number;
  goal_contributions: number;
}

export interface SquadLeaderData {
  metric: SquadLeaderMetric;
  label: string;
  value: number;
  unit: string;
  player: SquadPlayerData;
}

export interface SquadLensData {
  club: SquadClubData;
  season: string;
  minimum_minutes: number;
  record_total: number;
  qualified_total: number;
  excluded_total: number;
  total_minutes: number;
  total_goals: number;
  total_assists: number;
  unique_nationalities: number;
  top_five_minutes_share: number;
  position_groups: SquadPositionGroup[];
  leaders: SquadLeaderData[];
  core_players: SquadPlayerData[];
  summary: string[];
  source_name: string;
  source_url: string;
  source_version: number;
  license_name: string;
  license_url: string;
  sample_notice: string;
  method_notice: string;
}

export interface ClubMatchPreview {
  source_match_id: string;
  season: string;
  kickoff_at: string | null;
  home_club_name: string;
  home_club_slug: string;
  home_score: number;
  away_club_name: string;
  away_club_slug: string;
  away_score: number;
  venue: string;
}

export interface StandingClub {
  id: number;
  name: string;
  short_name: string;
  slug: string;
  primary_color: string;
}

export interface StandingItem {
  position: number;
  club: StandingClub;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goals_for: number;
  goals_against: number;
  goal_difference: number;
  points: number;
  source_kind: "historical" | "sample";
}

export interface StandingTableData {
  season: string;
  items: StandingItem[];
  total: number;
  is_partial: boolean;
  snapshot_date: string;
  source_name: string;
  source_url: string;
  sample_notice: string;
}

export interface MatchTeamData {
  id: number;
  name: string;
  short_name: string;
  slug: string;
  primary_color: string;
  score: number;
  shots: number;
  goals: number;
  total_xg: number;
}

export interface MatchShotData {
  source_event_id: string;
  period: number;
  minute: number;
  second: number;
  team_name: string;
  team_slug: string;
  team_color: string;
  player_name: string | null;
  outcome: string;
  is_goal: boolean;
  x: number;
  y: number;
  xg: number;
  body_part: string | null;
  shot_type: string | null;
  play_pattern: string | null;
}

export interface MatchSummaryData {
  source_match_id: string;
  competition: string;
  season: string;
  matchweek: number;
  kickoff_at: string | null;
  venue: string;
  status: string;
  home_team: MatchTeamData;
  away_team: MatchTeamData;
  shot_count: number;
  goal_count: number;
  total_xg: number;
  source_kind: "open-data";
}

export interface MatchListData {
  items: MatchSummaryData[];
  total: number;
  source_name: string;
  source_url: string;
  license_url: string;
  sample_notice: string;
}

export interface MatchDetailData extends MatchSummaryData {
  shots: MatchShotData[];
  source_name: string;
  source_url: string;
  license_url: string;
  source_last_updated: string;
  coordinate_note: string;
  interpretation_note: string;
}

export type FormResult = "W" | "D" | "L";

export interface FormClubData {
  id: number;
  name: string;
  short_name: string;
  slug: string;
  primary_color: string;
}

export interface FormRecordData {
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goals_for: number;
  goals_against: number;
  goal_difference: number;
  points: number;
  points_per_game: number;
}

export interface SeasonFormClubItem {
  position: number;
  club: FormClubData;
  overall: FormRecordData;
  home: FormRecordData;
  away: FormRecordData;
  recent_form: FormResult[];
  recent_points: number;
  points_by_matchweek: number[];
}

export interface SeasonFormOverviewData {
  competition: string;
  season: string;
  snapshot_date: string;
  match_count: number;
  goal_count: number;
  goals_per_match: number;
  home_wins: number;
  draws: number;
  away_wins: number;
  items: SeasonFormClubItem[];
  source_name: string;
  source_url: string;
  license_name: string;
  license_url: string;
  source_commit: string;
  sample_notice: string;
}

export interface ClubFormMatchData {
  source_match_id: string;
  matchweek: number;
  kickoff_at: string | null;
  venue: string;
  is_home: boolean;
  opponent: FormClubData;
  home_club: FormClubData;
  away_club: FormClubData;
  home_score: number;
  away_score: number;
  result: FormResult;
  points: number;
}

export interface ClubSeasonFormData {
  competition: string;
  season: string;
  snapshot_date: string;
  club: FormClubData;
  final_position: number;
  overall: FormRecordData;
  home: FormRecordData;
  away: FormRecordData;
  recent_form: FormResult[];
  longest_unbeaten: number;
  points_by_matchweek: number[];
  matches: ClubFormMatchData[];
  source_name: string;
  source_url: string;
  license_name: string;
  license_url: string;
  source_commit: string;
  sample_notice: string;
}

export interface MatchupClubSnapshot {
  club: FormClubData;
  final_position: number;
  overall: FormRecordData;
  home: FormRecordData;
  away: FormRecordData;
  recent_form: FormResult[];
  recent_points: number;
  longest_unbeaten: number;
}

export interface MatchupMeetingData {
  source_match_id: string;
  matchweek: number;
  kickoff_at: string | null;
  home_club: FormClubData;
  away_club: FormClubData;
  home_score: number;
  away_score: number;
  winner_slug: string | null;
}

export interface MatchupHeadToHeadData {
  meetings: MatchupMeetingData[];
  club_a_wins: number;
  draws: number;
  club_b_wins: number;
  club_a_goals: number;
  club_b_goals: number;
}

export interface MatchupDimensionData {
  key: string;
  label: string;
  club_a_value: string;
  club_b_value: string;
  advantage: "club_a" | "club_b" | "even";
  note: string;
}

export interface ClubMatchupData {
  competition: string;
  season: string;
  snapshot_date: string;
  club_a: MatchupClubSnapshot;
  club_b: MatchupClubSnapshot;
  head_to_head: MatchupHeadToHeadData;
  dimensions: MatchupDimensionData[];
  summary: string[];
  source_name: string;
  source_url: string;
  license_name: string;
  license_url: string;
  source_commit: string;
  sample_notice: string;
}

export type PlayerPosition = "FWD" | "MID" | "DEF" | "GK";

export type PlayerSortKey =
  | "full_name"
  | "club"
  | "position"
  | "minutes"
  | "goals"
  | "assists"
  | "goals_per90"
  | "assists_per90"
  | "shots_per90"
  | "key_passes_per90"
  | "tackles_per90"
  | "interceptions_per90"
  | "expected_goals_per90";

export type PlayerSortOrder = "asc" | "desc";

export interface PlayerClubData {
  name: string;
  short_name: string;
  slug: string;
  primary_color: string;
}

export interface PlayerSeasonTotals {
  appearances: number;
  starts: number;
  minutes: number;
  goals: number;
  assists: number;
  shots: number;
  key_passes: number;
  tackles: number;
  interceptions: number;
  expected_goals: number | null;
}

export interface PlayerPer90Metrics {
  goals_per90: number;
  assists_per90: number;
  shots_per90: number;
  key_passes_per90: number;
  tackles_per90: number;
  interceptions_per90: number;
  expected_goals_per90: number;
}

export interface PlayerMetricPercentiles {
  goals_per90: number;
  assists_per90: number;
  shots_per90: number;
  key_passes_per90: number;
  tackles_per90: number;
  interceptions_per90: number;
  expected_goals_per90: number;
}

export interface PlayerPercentileProfile {
  scope: "position_pool" | "all_qualified_players";
  peer_count: number;
  metrics: PlayerMetricPercentiles;
}

export interface PlayerLabItem {
  id: number;
  full_name: string;
  slug: string;
  shirt_number: number | null;
  position: PlayerPosition;
  nationality: string;
  date_of_birth: string | null;
  birth_year: number | null;
  source_kind: "kaggle-fbref";
  club: PlayerClubData;
  season: string;
  totals: PlayerSeasonTotals;
  per90: PlayerPer90Metrics;
  percentiles: PlayerPercentileProfile;
}

export interface PlayerLabData {
  items: PlayerLabItem[];
  total: number;
  pool_total: number;
  dataset_total: number;
  unique_player_total: number;
  transfer_record_total: number;
  season: string;
  minimum_minutes: number;
  limit: number;
  offset: number;
  sort_by: PlayerSortKey;
  order: PlayerSortOrder;
  available_positions: PlayerPosition[];
  available_clubs: PlayerClubData[];
  source_name: string;
  source_url: string;
  source_version: number;
  license_name: string;
  license_url: string;
  sample_notice: string;
  percentile_notice: string;
}

export interface PlayerLabQuery {
  season?: string;
  minimumMinutes?: number;
  query?: string;
  position?: PlayerPosition;
  clubSlug?: string;
  sortBy?: PlayerSortKey;
  order?: PlayerSortOrder;
  limit?: number;
  offset?: number;
}

export interface PlayerSimilarityMetricWeight {
  key: keyof PlayerPer90Metrics;
  label: string;
  weight: number;
}

export interface PlayerSimilarityDifference {
  key: keyof PlayerPer90Metrics;
  label: string;
  target_percentile: number;
  candidate_percentile: number;
  gap: number;
}

export interface PlayerSimilarityCandidate {
  player: PlayerLabItem;
  similarity_score: number;
  closest_metrics: string[];
  key_difference: PlayerSimilarityDifference;
}

export interface PlayerSimilarityData {
  target: PlayerLabItem;
  items: PlayerSimilarityCandidate[];
  candidate_total: number;
  season: string;
  minimum_minutes: number;
  position: PlayerPosition;
  is_supported: boolean;
  unavailable_reason: string | null;
  metric_weights: PlayerSimilarityMetricWeight[];
  method_notice: string;
  sample_notice: string;
}

export type AgentFocus =
  | "balanced"
  | "scoring"
  | "creativity"
  | "pressing";

export type AgentRequestedFocus = AgentFocus | "auto";

export interface AgentPlayerOption {
  slug: string;
  full_name: string;
  club_name: string;
  club_color: string;
  position: string;
  minutes: number;
}

export interface AgentPlayerOptionData {
  items: AgentPlayerOption[];
  total: number;
  season: string;
  sample_notice: string;
}

export interface AgentPlayerProfile extends AgentPlayerOption {
  nationality: string;
}

export interface AgentMetricValue {
  player_slug: string;
  value: number;
  percentile: number;
}

export interface AgentMetricComparison {
  key: string;
  label: string;
  unit: string;
  weight: number;
  values: AgentMetricValue[];
  leader_slug: string | null;
}

export interface AgentStep {
  index: number;
  title: string;
  tool: string;
  detail: string;
  status: "completed";
}

export interface AgentEvidence {
  title: string;
  detail: string;
  leader_slug: string | null;
}

export interface AgentRecommendation {
  winner_slug: string;
  headline: string;
  summary: string;
  confidence: number;
  scores: Record<string, number>;
}

export interface AgentGeneration {
  mode: "local_rules" | "qwen_enhanced";
  status: "completed" | "not_configured" | "fallback" | "pending";
  provider: "local" | "qwen";
  model: string | null;
  note: string;
}

export interface AgentCapabilitiesData {
  qwen_configured: boolean;
  provider: "qwen";
  model: string;
  default_mode: "local_rules" | "qwen_enhanced";
  message: string;
}

export interface AgentRunContext {
  parent_run_id: string | null;
  follow_up_depth: number;
  parent_question: string | null;
  parent_headline: string | null;
  inherited_scope: boolean;
  note: string;
}

export interface AgentAnalysisData {
  run_id: string;
  task_type: "player_comparison";
  question: string;
  season: string;
  requested_focus: AgentRequestedFocus;
  focus: AgentFocus;
  focus_label: string;
  players: AgentPlayerProfile[];
  steps: AgentStep[];
  metrics: AgentMetricComparison[];
  evidence: AgentEvidence[];
  recommendation: AgentRecommendation;
  generation: AgentGeneration;
  limitations: string[];
  sample_notice: string;
  context: AgentRunContext;
}

export interface AgentAnalysisRequest {
  question: string;
  player_slugs: [string, string];
  season: string;
  focus: AgentRequestedFocus;
}

export interface AgentFollowUpRequest {
  question: string;
  focus: AgentRequestedFocus;
}

export interface AgentRunSummary {
  run_id: string;
  parent_run_id: string | null;
  follow_up_depth: number;
  created_at: string;
  question: string;
  season: string;
  focus: AgentFocus;
  focus_label: string;
  players: AgentPlayerProfile[];
  winner_slug: string;
  generation_mode: "local_rules" | "qwen_enhanced";
}

export interface AgentRunListData {
  items: AgentRunSummary[];
  total: number;
  limit: number;
  offset: number;
  storage_notice: string;
}

export interface AgentRunDetailData {
  run_id: string;
  parent_run_id: string | null;
  follow_up_depth: number;
  created_at: string;
  result: AgentAnalysisData;
  source_name: string;
  source_url: string;
  source_note: string;
  storage_notice: string;
}

export type CopilotToolName =
  | "get_league_table"
  | "get_club_form"
  | "analyze_club_squad"
  | "compare_clubs"
  | "compare_players"
  | "find_similar_players"
  | "get_match_shot_summary";

export type CopilotMode = "local_tool_router" | "qwen_tool_calling";

export interface CopilotToolCapability {
  name: CopilotToolName;
  label: string;
  description: string;
  data_scope: string;
}

export interface CopilotCapabilitiesData {
  qwen_configured: boolean;
  model: string;
  default_mode: CopilotMode;
  tools: CopilotToolCapability[];
  message: string;
}

export interface CopilotSource {
  name: string;
  url: string;
  license_name: string | null;
  license_url: string | null;
  data_scope: string;
}

export interface CopilotEvidence {
  label: string;
  value: string;
  detail: string;
  tool: CopilotToolName;
}

export interface CopilotToolTrace {
  index: number;
  call_id: string;
  tool: CopilotToolName;
  label: string;
  arguments: Record<string, string | number | boolean | null>;
  summary: string;
  evidence: CopilotEvidence[];
  source: CopilotSource;
  status: "completed";
}

export interface CopilotGeneration {
  mode: CopilotMode;
  status: "completed" | "not_configured" | "fallback";
  provider: "local" | "qwen";
  model: string | null;
  note: string;
}

export interface CopilotLink {
  label: string;
  href: string;
}

export interface CopilotAnswerData {
  run_id: string;
  question: string;
  season: string;
  headline: string;
  answer: string;
  generation: CopilotGeneration;
  tool_calls: CopilotToolTrace[];
  evidence: CopilotEvidence[];
  links: CopilotLink[];
  limitations: string[];
  suggestions: string[];
  scope_notice: string;
}

export interface CopilotQueryRequest {
  question: string;
  season: string;
}
