import axios, { AxiosError, type AxiosInstance, type AxiosRequestConfig } from 'axios';
import { getSession, signOut } from 'next-auth/react';
import type {
  ApiResponse,
  Assessment,
  AssessmentFormData,
  DashboardStats,
  Intervention,
  PaginatedResponse,
  ParentObservation,
  ParentObservationFormData,
  Prediction,
  Student,
  StudentWithStats,
  SupportQueueItem,
  SupportSummary,
  User,
} from './types';

// ─── Axios instance ───────────────────────────────────────────────────────────

const API_BASE_URL =
  typeof window === 'undefined'
    ? process.env.INTERNAL_API_URL ||
      process.env.NEXT_PUBLIC_API_URL ||
      'http://localhost:8000'
    : process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

// ─── Request interceptor ──────────────────────────────────────────────────────

apiClient.interceptors.request.use(
  async (config) => {
    if (typeof window !== 'undefined') {
      const session = await getSession();
      if (session?.accessToken) {
        config.headers.Authorization = `Bearer ${session.accessToken}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ─── Response interceptor ─────────────────────────────────────────────────────

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      await signOut({ callbackUrl: '/login' });
    }
    return Promise.reject(error);
  }
);

// ─── Generic request helper ───────────────────────────────────────────────────

async function request<T>(config: AxiosRequestConfig): Promise<T> {
  const response = await apiClient.request<ApiResponse<T>>(config);
  return response.data.data;
}

function mapPaginated<T>(response: any, mapper: (item: any) => T): PaginatedResponse<T> {
  return {
    data: (response.data || []).map(mapper),
    meta: {
      total: response.meta?.total || 0,
      page: response.meta?.page || 1,
      limit: response.meta?.limit || response.meta?.per_page || 20,
      totalPages: response.meta?.totalPages || response.meta?.total_pages || 0,
    },
  };
}

// ─── Auth ─────────────────────────────────────────────────────────────────────

export interface LoginCredentials {
  email: string;
  password: string;
}

interface BackendTokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

interface BackendRegisterResponse {
  data: User & { full_name: string };
  tokens: BackendTokenResponse;
}

export interface LoginResponse {
  user: User & { full_name: string };
  access_token: string;
  refresh_token: string;
}

export async function loginUser(credentials: LoginCredentials): Promise<LoginResponse> {
  // Step 1: get tokens
  const tokenRes = await apiClient.post<BackendTokenResponse | BackendRegisterResponse>(
    '/auth/login',
    credentials
  );
  const tokenData =
    'tokens' in tokenRes.data ? tokenRes.data.tokens : tokenRes.data;
  const { access_token, refresh_token } = tokenData;

  // Step 2: fetch profile using the new token
  const meRes = await apiClient.get<User & { full_name: string }>('/auth/me', {
    headers: { Authorization: `Bearer ${access_token}` },
  });

  return {
    user: meRes.data,
    access_token,
    refresh_token,
  };
}

// ─── Students ─────────────────────────────────────────────────────────────────

export interface GetStudentsParams {
  page?: number;
  limit?: number;
  grade?: string;
  riskLevel?: string;
  search?: string;
}

export async function getStudents(
  params: GetStudentsParams = {}
): Promise<PaginatedResponse<StudentWithStats>> {
  const response = await apiClient.get('/students/', {
    params: {
      page: params.page,
      per_page: params.limit,
      grade_level: parseGradeLevel(params.grade),
      risk_level: params.riskLevel,
    },
  });
  return mapPaginated(response.data, mapStudent);
}

export async function getStudent(id: string): Promise<StudentWithStats> {
  const response = await apiClient.get(`/students/${id}`);
  return mapStudent(response.data);
}

export async function getStudentAssessments(
  studentId: string
): Promise<Assessment[]> {
  return request<Assessment[]>({
    method: 'GET',
    url: `/students/${studentId}/assessments`,
  });
}

export async function getStudentObservations(
  studentId: string
): Promise<ParentObservation[]> {
  return request<ParentObservation[]>({
    method: 'GET',
    url: `/students/${studentId}/observations`,
  });
}

// ─── Assessments ─────────────────────────────────────────────────────────────

function mapPrediction(item: any): Prediction | undefined {
  if (!item) return undefined;
  return {
    id: item.id || item.assessment_id || '',
    assessmentId: item.assessment_id || item.assessmentId || '',
    studentId: item.student_id || item.studentId || '',
    riskLevel: item.risk_level || item.riskLevel || 'medium',
    riskProbability: item.risk_probability ?? item.riskProbability ?? 0,
    confidence: typeof item.confidence === 'number' ? item.confidence : 0,
    featureImportances: item.feature_importances || item.featureImportances || [],
    recommendedInterventions: item.recommended_interventions || item.recommendedInterventions || [],
    modelVersion: item.model_version || item.modelVersion || 'unknown',
    createdAt: item.created_at || item.createdAt || new Date().toISOString(),
  };
}

function parseGradeLevel(grade?: string): number | undefined {
  if (!grade) return undefined;
  const match = grade.match(/\d+/);
  return match ? Number(match[0]) : undefined;
}

function mapStudent(item: any): StudentWithStats {
  const latestAssessment = item.latest_assessment || item.latestAssessment;
  const latestPrediction = item.latest_prediction || item.latestPrediction || latestAssessment?.prediction;
  const mathScore = latestAssessment?.math_score ?? latestAssessment?.mathScore;
  const readingScore = latestAssessment?.reading_score ?? latestAssessment?.readingScore;
  const writingScore = latestAssessment?.writing_score ?? latestAssessment?.writingScore;
  const assessedAt =
    latestAssessment?.assessment_date ||
    latestAssessment?.assessmentDate ||
    item.last_assessment_date ||
    item.lastAssessmentDate;

  return {
    id: item.id,
    name: item.name || item.full_name || item.fullName || 'Unnamed student',
    grade: item.grade || (item.grade_level ? `Grade ${item.grade_level}` : item.gradeLevel ? `Grade ${item.gradeLevel}` : ''),
    enrollmentDate: item.enrollment_date || item.enrollmentDate || new Date().toISOString(),
    guardianName: item.guardian_name || item.guardianName,
    guardianContact: item.guardian_contact || item.guardianContact,
    schoolId: item.school_id || item.schoolId || '',
    teacherId: item.teacher_id || item.teacherId,
    currentRiskLevel: latestPrediction?.risk_level || latestPrediction?.riskLevel || item.current_risk_level || item.currentRiskLevel,
    lastAssessmentDate: assessedAt,
    totalAssessments: item.total_assessments ?? item.totalAssessments ?? (latestAssessment ? 1 : 0),
    averageMathScore: item.average_math_score ?? item.averageMathScore ?? mathScore,
    averageReadingScore: item.average_reading_score ?? item.averageReadingScore ?? readingScore,
    averageWritingScore: item.average_writing_score ?? item.averageWritingScore ?? writingScore,
    latestRiskProbability:
      latestPrediction?.risk_probability ??
      latestPrediction?.riskProbability ??
      item.latest_risk_probability ??
      item.latestRiskProbability,
    trend: item.trend || 'stable',
    createdAt: item.created_at || item.createdAt || new Date().toISOString(),
    updatedAt: item.updated_at || item.updatedAt || new Date().toISOString(),
  };
}

function mapAssessment(item: any): Assessment {
  const scores = [item.math_score, item.reading_score, item.writing_score].filter(
    (score) => typeof score === 'number'
  );
  const average = scores.length
    ? Math.round(scores.reduce((sum, score) => sum + score, 0) / scores.length)
    : 0;
  return {
    id: item.id,
    studentId: item.student_id || item.studentId,
    studentName: item.student_name || item.studentName,
    teacherId: item.assessed_by_id || item.teacherId || '',
    mathScore: item.math_score ?? item.mathScore ?? average,
    readingScore: item.reading_score ?? item.readingScore ?? average,
    writingScore: item.writing_score ?? item.writingScore ?? average,
    attendancePct: item.attendance_pct ?? item.attendancePct ?? 0,
    behaviorRating: item.behavior_rating ?? item.behaviorRating ?? 3,
    literacyLevel: item.literacy_level ?? item.literacyLevel ?? 0,
    notes: item.notes,
    prediction: mapPrediction(item.prediction),
    createdAt: item.created_at || item.createdAt || item.assessment_date || new Date().toISOString(),
    updatedAt: item.updated_at || item.updatedAt || item.created_at || new Date().toISOString(),
  };
}

export async function getAssessments(params: {
  page?: number;
  limit?: number;
}): Promise<PaginatedResponse<Assessment>> {
  const response = await apiClient.get('/assessments/', {
    params: {
      page: params.page,
      per_page: params.limit,
    },
  });
  return mapPaginated(response.data, mapAssessment);
}

function mapSupportItem(item: any): SupportQueueItem {
  return {
    studentId: item.student_id,
    studentName: item.student_name,
    gradeLevel: item.grade_level,
    schoolId: item.school_id,
    latestAssessmentId: item.latest_assessment_id || undefined,
    latestAssessmentDate: item.latest_assessment_date || undefined,
    riskLevel: item.risk_level,
    riskProbability: item.risk_probability,
    supportLevel: item.support_level,
    confidence: item.confidence,
    dataCompleteness: item.data_completeness,
    attendancePct: item.attendance_pct ?? undefined,
    academicAverage: item.academic_average ?? undefined,
    literacyLevel: item.literacy_level ?? undefined,
    riskDrivers: item.risk_drivers || [],
    recommendedActions: item.recommended_actions || [],
    openInterventions: item.open_interventions || 0,
    updatedAt: item.updated_at || undefined,
  };
}

export async function getSupportQueue(params: {
  limit?: number;
  supportLevel?: 'urgent' | 'watch' | 'routine';
} = {}): Promise<SupportQueueItem[]> {
  const response = await apiClient.get<any[]>('/support/queue', {
    params: {
      limit: params.limit,
      support_level: params.supportLevel,
    },
  });
  return response.data.map(mapSupportItem);
}

export async function getSupportSummary(): Promise<SupportSummary> {
  const response = await apiClient.get<any>('/support/summary');
  return {
    totalStudents: response.data.total_students,
    urgent: response.data.urgent,
    watch: response.data.watch,
    routine: response.data.routine,
    openInterventions: response.data.open_interventions,
    dataCompletenessAvg: response.data.data_completeness_avg,
  };
}

export async function createInterventionFromSignal(data: {
  studentId: string;
  assessmentId?: string;
  action: string;
  interventionType?: 'academic' | 'behavioral' | 'attendance' | 'home';
  ownerNote?: string;
}): Promise<Intervention> {
  const response = await apiClient.post('/support/interventions/from-signal', {
    student_id: data.studentId,
    assessment_id: data.assessmentId,
    action: data.action,
    intervention_type: data.interventionType || 'academic',
    owner_note: data.ownerNote,
  });
  const item = response.data;
  const category =
    item.type === 'home'
      ? 'family'
      : item.type === 'attendance'
        ? 'social'
        : item.type;
  return {
    id: item.id,
    studentId: item.student_id,
    teacherId: item.created_by_id,
    title: item.type,
    description: item.description,
    category,
    status: item.status === 'discontinued' ? 'paused' : item.status,
    startDate: item.start_date,
    endDate: item.end_date,
    notes: item.outcome_notes,
    createdAt: item.created_at,
    updatedAt: item.updated_at,
  };
}

export async function createAssessment(
  data: AssessmentFormData
): Promise<Assessment> {
  const response = await apiClient.post('/assessments/', {
    student_id: data.studentId,
    math_score: data.mathScore,
    reading_score: data.readingScore,
    writing_score: data.writingScore,
    attendance_pct: data.attendancePct,
    behavior_rating: data.behaviorRating,
    literacy_level: data.literacyLevel,
    notes: data.notes,
  });
  return mapAssessment(response.data);
}

export async function getAssessment(id: string): Promise<Assessment> {
  const response = await apiClient.get(`/assessments/${id}`);
  return mapAssessment(response.data);
}

// ─── Predictions ─────────────────────────────────────────────────────────────

export async function getPrediction(assessmentId: string): Promise<Prediction> {
  return request<Prediction>({
    method: 'GET',
    url: `/assessments/${assessmentId}/prediction`,
  });
}

// ─── Observations ────────────────────────────────────────────────────────────

export async function createObservation(
  data: ParentObservationFormData
): Promise<ParentObservation> {
  return request<ParentObservation>({
    method: 'POST',
    url: '/observations',
    data,
  });
}

export async function getRecentObservations(
  studentId: string,
  days = 7
): Promise<ParentObservation[]> {
  return request<ParentObservation[]>({
    method: 'GET',
    url: `/students/${studentId}/observations`,
    params: { days },
  });
}

// ─── Dashboard ────────────────────────────────────────────────────────────────

export async function getDashboardStats(): Promise<DashboardStats> {
  return request<DashboardStats>({ method: 'GET', url: '/dashboard/stats' });
}

// ─── Users ────────────────────────────────────────────────────────────────────

export async function getCurrentUser(): Promise<User> {
  return request<User>({ method: 'GET', url: '/users/me' });
}

// ─── Mock data helpers (for development without backend) ──────────────────────

export function generateMockStudents(): StudentWithStats[] {
  const grades = ['Grade 1', 'Grade 2', 'Grade 3', 'Grade 4', 'Grade 5', 'Grade 6'];
  const riskLevels: Array<'low' | 'medium' | 'high' | 'critical'> = [
    'low', 'low', 'low', 'medium', 'medium', 'high', 'critical',
  ];
  const trends: Array<'improving' | 'declining' | 'stable'> = [
    'improving', 'declining', 'stable',
  ];

  const names = [
    'Amara Osei', 'Kwame Asante', 'Fatima Hassan', 'Chidi Okafor',
    'Naledi Dlamini', 'Kofi Mensah', 'Aisha Diallo', 'Emeka Eze',
    'Zara Mbeki', 'Tendai Mwangi', 'Abebe Girma', 'Yetunde Adeyemi',
    'Sione Taufa', 'Amina Kamau', 'Olumide Bello',
  ];

  return names.map((name, i) => ({
    id: `student-${i + 1}`,
    name,
    grade: grades[i % grades.length],
    enrollmentDate: '2024-01-15',
    guardianName: `Guardian of ${name}`,
    guardianContact: `+254 7${Math.floor(Math.random() * 90000000 + 10000000)}`,
    schoolId: 'school-1',
    currentRiskLevel: riskLevels[i % riskLevels.length],
    lastAssessmentDate: new Date(
      Date.now() - Math.floor(Math.random() * 30) * 86400000
    ).toISOString(),
    totalAssessments: Math.floor(Math.random() * 10) + 1,
    averageMathScore: Math.floor(Math.random() * 40) + 50,
    averageReadingScore: Math.floor(Math.random() * 40) + 50,
    averageWritingScore: Math.floor(Math.random() * 40) + 50,
    latestRiskProbability: Math.random(),
    trend: trends[i % trends.length],
    createdAt: '2024-01-15T08:00:00Z',
    updatedAt: new Date().toISOString(),
  }));
}

export function generateMockDashboardStats(): DashboardStats {
  return {
    totalStudents: 248,
    onTrackCount: 161,
    atRiskCount: 62,
    needInterventionCount: 25,
    onTrackPct: 65,
    atRiskPct: 25,
    riskDistribution: {
      low: 161,
      medium: 62,
      high: 18,
      critical: 7,
    },
    subjectAverages: {
      math: 67,
      reading: 71,
      writing: 64,
    },
  };
}

export function generateMockAssessments(): Assessment[] {
  const students = generateMockStudents().slice(0, 6);
  return students.map((s, i) => ({
    id: `assessment-${i + 1}`,
    studentId: s.id,
    studentName: s.name,
    teacherId: 'teacher-1',
    mathScore: Math.floor(Math.random() * 40) + 50,
    readingScore: Math.floor(Math.random() * 40) + 50,
    writingScore: Math.floor(Math.random() * 40) + 50,
    attendancePct: Math.floor(Math.random() * 30) + 70,
    behaviorRating: Math.floor(Math.random() * 3) + 3,
    literacyLevel: Math.floor(Math.random() * 5) + 5,
    notes: '',
    prediction: {
      id: `pred-${i + 1}`,
      assessmentId: `assessment-${i + 1}`,
      studentId: s.id,
      riskLevel: s.currentRiskLevel || 'low',
      riskProbability: s.latestRiskProbability || 0.2,
      confidence: 0.85,
      featureImportances: [
        { feature: 'math_score', importance: 0.32, value: 65 },
        { feature: 'attendance_pct', importance: 0.28, value: 82 },
        { feature: 'reading_score', importance: 0.2, value: 70 },
      ],
      recommendedInterventions: ['Extra tutoring', 'Peer support'],
      modelVersion: '2.1.0',
      createdAt: new Date().toISOString(),
    },
    createdAt: new Date(Date.now() - i * 86400000).toISOString(),
    updatedAt: new Date().toISOString(),
  }));
}
