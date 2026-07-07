// ─── Core Types ─────────────────────────────────────────────────────────────

export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';

export type UserRole = 'admin' | 'teacher' | 'parent' | 'student';

export type Language =
  | 'en'
  | 'sw'
  | 'fr'
  | 'am'
  | 'ha'
  | 'yo'
  | 'ig'
  | 'zu'
  | 'xh'
  | 'ar';

// ─── API Envelope ────────────────────────────────────────────────────────────

export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: 'success' | 'error';
}

export interface PaginatedResponse<T> {
  data: T[];
  meta: {
    total: number;
    page: number;
    limit: number;
    totalPages: number;
  };
}

// ─── User ────────────────────────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  schoolId?: string;
  schoolName?: string;
  avatarUrl?: string;
  language?: Language;
  createdAt: string;
  updatedAt: string;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

// ─── Student ─────────────────────────────────────────────────────────────────

export interface Student {
  id: string;
  name: string;
  grade: string;
  dateOfBirth?: string;
  enrollmentDate: string;
  guardianName?: string;
  guardianContact?: string;
  schoolId: string;
  teacherId?: string;
  currentRiskLevel?: RiskLevel;
  lastAssessmentDate?: string;
  createdAt: string;
  updatedAt: string;
}

export interface StudentWithStats extends Student {
  totalAssessments: number;
  averageMathScore?: number;
  averageReadingScore?: number;
  averageWritingScore?: number;
  latestRiskProbability?: number;
  trend?: 'improving' | 'declining' | 'stable';
}

// ─── Assessment ──────────────────────────────────────────────────────────────

export interface Assessment {
  id: string;
  studentId: string;
  studentName?: string;
  teacherId: string;
  mathScore: number;
  readingScore: number;
  writingScore: number;
  attendancePct: number;
  behaviorRating: number;
  literacyLevel: number;
  notes?: string;
  prediction?: Prediction;
  createdAt: string;
  updatedAt: string;
}

export interface AssessmentFormData {
  studentId: string;
  mathScore: number;
  readingScore: number;
  writingScore: number;
  attendancePct: number;
  behaviorRating: number;
  literacyLevel: number;
  notes?: string;
}

// ─── Prediction ──────────────────────────────────────────────────────────────

export interface FeatureImportance {
  feature: string;
  importance: number;
  value: number;
}

export interface Prediction {
  id: string;
  assessmentId: string;
  studentId: string;
  riskLevel: RiskLevel;
  riskProbability: number;
  confidence: number;
  featureImportances: FeatureImportance[];
  recommendedInterventions: string[];
  modelVersion: string;
  createdAt: string;
}

// ─── Parent Observation ──────────────────────────────────────────────────────

export interface ParentObservation {
  id: string;
  studentId: string;
  parentId: string;
  homeworkCompletion: number;
  readingMinutes: number;
  focusRating: number;
  behaviorHome: number;
  mood: number;
  sleepHours: number;
  notes?: string;
  observationDate: string;
  createdAt: string;
}

export interface ParentObservationFormData {
  studentId: string;
  homeworkCompletion: number;
  readingMinutes: number;
  focusRating: number;
  behaviorHome: number;
  mood: number;
  sleepHours: number;
  notes?: string;
}

// ─── Intervention ────────────────────────────────────────────────────────────

export interface Intervention {
  id: string;
  studentId: string;
  teacherId: string;
  title: string;
  description: string;
  category: 'academic' | 'behavioral' | 'social' | 'family';
  status: 'planned' | 'active' | 'completed' | 'paused';
  startDate: string;
  endDate?: string;
  notes?: string;
  createdAt: string;
  updatedAt: string;
}

export interface SupportQueueItem {
  studentId: string;
  studentName: string;
  gradeLevel: number;
  schoolId: string;
  latestAssessmentId?: string;
  latestAssessmentDate?: string;
  riskLevel: RiskLevel;
  riskProbability: number;
  supportLevel: 'urgent' | 'watch' | 'routine';
  confidence: string;
  dataCompleteness: number;
  attendancePct?: number;
  academicAverage?: number;
  literacyLevel?: number;
  riskDrivers: Array<Record<string, unknown>>;
  recommendedActions: string[];
  openInterventions: number;
  updatedAt?: string;
}

export interface SupportSummary {
  totalStudents: number;
  urgent: number;
  watch: number;
  routine: number;
  openInterventions: number;
  dataCompletenessAvg: number;
}

// ─── Dashboard ───────────────────────────────────────────────────────────────

export interface DashboardStats {
  totalStudents: number;
  onTrackCount: number;
  atRiskCount: number;
  needInterventionCount: number;
  onTrackPct: number;
  atRiskPct: number;
  riskDistribution: {
    low: number;
    medium: number;
    high: number;
    critical: number;
  };
  subjectAverages: {
    math: number;
    reading: number;
    writing: number;
  };
}

// ─── Resource ────────────────────────────────────────────────────────────────

export interface Resource {
  id: string;
  title: string;
  description: string;
  category: 'reading' | 'math' | 'behavior' | 'parent';
  estimatedMinutes: number;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  url?: string;
  saved?: boolean;
}

// ─── Chart Data ──────────────────────────────────────────────────────────────

export interface ScoreDataPoint {
  date: string;
  math: number;
  reading: number;
  writing: number;
  riskProbability?: number;
}

export interface RadarDataPoint {
  subject: string;
  student: number;
  baseline: number;
}
