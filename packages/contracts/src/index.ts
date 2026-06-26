export const KairosStatus = {
  Sleeping: "KAIROS_SLEEPING",
  Attentive: "KAIROS_ATTENTIVE",
  Awake: "KAIROS_AWAKE",
  Locked: "KAIROS_LOCKED"
} as const;

export type KairosStatus = (typeof KairosStatus)[keyof typeof KairosStatus];

export const Decision = {
  NoBet: "NO_BET",
  InsufficientData: "INSUFFICIENT_DATA",
  Advice: "ADVICE",
  Watch: "WATCH",
  Suspended: "SUSPENDED"
} as const;

export type Decision = (typeof Decision)[keyof typeof Decision];

export interface PredictionEnvelope {
  prediction_id: string;
  model_version: string;
  feature_snapshot_id: string;
  prediction_time: string;
  mode: "PRE_MATCH" | "LIVE";
  market: string;
  probabilities: Record<string, number>;
  calibration_bucket: string | null;
  decision: Decision;
  reasons: string[];
  data_freshness: Record<string, unknown>;
  odds_snapshot_id: string | null;
  immutable_hash: string;
}

export interface KairosSignal {
  signal_id: string;
  engine_name: "Kairos";
  status: KairosStatus;
  decision: Decision;
  created_at: string;
  reasons: string[];
  data_freshness: Record<string, unknown>;
}

export interface BetCenterBudget {
  budget_id: string;
  currency: "CDF" | string;
  amount: number;
  real_betting_enabled: false;
}

export interface StakeRange {
  currency: "CDF" | string;
  min_stake: number;
  max_stake: number;
  decision: Decision;
  real_betting_enabled: false;
}

export interface PostMatchOutcome {
  outcome_id: string;
  provider: string;
  provider_event_id: string;
  observed_at: string;
  fetched_at: string;
  available_at: string;
  source_version: string;
  quality_flags: string[];
  raw_hash: string;
}
