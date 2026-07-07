export type EduSightClientOptions = {
  baseUrl: string;
  apiKey: string;
};

export type PredictionPayload = {
  external_student_id?: string;
  student_id?: string;
  grade_level?: number;
  age?: number;
  gender?: string;
  attendance_pct?: number;
  attendance_rate?: number;
  academic_average?: number;
  previous_term_average?: number;
  behavior_incidents?: number;
  guardian_engagement_score?: number;
  context?: Record<string, unknown>;
};

export type SupportSignal = {
  model_version: string;
  support_level: string;
  risk_level: string;
  risk_probability: number;
  calibrated_probability: number;
  confidence: string;
  data_completeness: number;
  missing_data_warnings: Array<Record<string, unknown>>;
  risk_drivers: Array<Record<string, unknown>>;
  recommended_actions: string[];
  suggested_intervention_plan: Array<Record<string, unknown>>;
  explanation: string;
  teacher_explanation: string;
  parent_explanation: string;
};

export class EduSightClient {
  private baseUrl: string;
  private apiKey: string;

  constructor(options: EduSightClientOptions) {
    this.baseUrl = options.baseUrl.replace(/\/$/, '');
    this.apiKey = options.apiKey;
  }

  async predict(payload: PredictionPayload): Promise<SupportSignal> {
    return this.request<SupportSignal>('/api/v1/integrations/predict', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async ingestEvent(payload: Record<string, unknown>) {
    return this.request('/api/v1/integrations/events', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async modelVersion() {
    return this.request('/api/v1/integrations/model-version');
  }

  private async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      ...init,
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': this.apiKey,
        ...(init.headers || {}),
      },
    });
    if (!response.ok) {
      throw new Error(`EduSight API error ${response.status}: ${await response.text()}`);
    }
    return response.json() as Promise<T>;
  }
}
