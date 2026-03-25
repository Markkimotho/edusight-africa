import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getStudents,
  getStudent,
  getStudentAssessments,
  getStudentObservations,
  type GetStudentsParams,
  generateMockStudents,
} from '@/lib/api';
import { useStudentFilterStore } from '@/lib/store';
import type { PaginatedResponse, StudentWithStats } from '@/lib/types';

// ─── Keys ────────────────────────────────────────────────────────────────────

export const studentKeys = {
  all: ['students'] as const,
  lists: () => [...studentKeys.all, 'list'] as const,
  list: (params: GetStudentsParams) => [...studentKeys.lists(), params] as const,
  details: () => [...studentKeys.all, 'detail'] as const,
  detail: (id: string) => [...studentKeys.details(), id] as const,
  assessments: (id: string) => [...studentKeys.detail(id), 'assessments'] as const,
  observations: (id: string) => [...studentKeys.detail(id), 'observations'] as const,
};

// ─── Hooks ───────────────────────────────────────────────────────────────────

export function useStudents(params: GetStudentsParams = {}) {
  return useQuery({
    queryKey: studentKeys.list(params),
    queryFn: async () => {
      try {
        return await getStudents(params);
      } catch {
        // Fallback to mock data in development
        const mockStudents = generateMockStudents();
        const filtered = mockStudents.filter((s) => {
          if (params.grade && s.grade !== params.grade) return false;
          if (params.riskLevel && s.currentRiskLevel !== params.riskLevel) return false;
          if (
            params.search &&
            !s.name.toLowerCase().includes(params.search.toLowerCase())
          )
            return false;
          return true;
        });
        const page = params.page || 1;
        const limit = params.limit || 10;
        const start = (page - 1) * limit;
        return {
          data: filtered.slice(start, start + limit),
          meta: {
            total: filtered.length,
            page,
            limit,
            totalPages: Math.ceil(filtered.length / limit),
          },
        } as PaginatedResponse<StudentWithStats>;
      }
    },
    staleTime: 30_000,
    placeholderData: (prev) => prev,
  });
}

export function useStudentsWithFilters() {
  const { grade, riskLevel, search, page } = useStudentFilterStore();
  return useStudents({
    grade: grade || undefined,
    riskLevel: riskLevel || undefined,
    search: search || undefined,
    page,
    limit: 10,
  });
}

export function useStudent(id: string) {
  return useQuery({
    queryKey: studentKeys.detail(id),
    queryFn: async () => {
      try {
        return await getStudent(id);
      } catch {
        const mock = generateMockStudents().find((s) => s.id === id);
        if (mock) return mock;
        throw new Error('Student not found');
      }
    },
    enabled: !!id,
    staleTime: 60_000,
  });
}

export function useStudentAssessments(studentId: string) {
  return useQuery({
    queryKey: studentKeys.assessments(studentId),
    queryFn: async () => {
      try {
        return await getStudentAssessments(studentId);
      } catch {
        // Return empty array for mock
        return [];
      }
    },
    enabled: !!studentId,
    staleTime: 30_000,
  });
}

export function useStudentObservations(studentId: string) {
  return useQuery({
    queryKey: studentKeys.observations(studentId),
    queryFn: async () => {
      try {
        return await getStudentObservations(studentId);
      } catch {
        return [];
      }
    },
    enabled: !!studentId,
    staleTime: 30_000,
  });
}
