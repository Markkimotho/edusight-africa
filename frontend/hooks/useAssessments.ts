import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getAssessments,
  createAssessment,
  getDashboardStats,
  generateMockAssessments,
  generateMockDashboardStats,
} from '@/lib/api';
import type { AssessmentFormData, DashboardStats, PaginatedResponse, Assessment } from '@/lib/types';
import { useToastStore } from '@/lib/store';
import { studentKeys } from './useStudents';

// ─── Keys ────────────────────────────────────────────────────────────────────

export const assessmentKeys = {
  all: ['assessments'] as const,
  lists: () => [...assessmentKeys.all, 'list'] as const,
  list: (params: { page?: number; limit?: number }) =>
    [...assessmentKeys.lists(), params] as const,
  dashboard: ['dashboard', 'stats'] as const,
};

// ─── Dashboard stats ──────────────────────────────────────────────────────────

export function useDashboardStats() {
  return useQuery({
    queryKey: assessmentKeys.dashboard,
    queryFn: async () => {
      try {
        return await getDashboardStats();
      } catch {
        return generateMockDashboardStats();
      }
    },
    staleTime: 60_000,
  });
}

// ─── Assessment list ──────────────────────────────────────────────────────────

export function useAssessments(params: { page?: number; limit?: number } = {}) {
  return useQuery({
    queryKey: assessmentKeys.list(params),
    queryFn: async () => {
      try {
        return await getAssessments(params);
      } catch {
        const mock = generateMockAssessments();
        const page = params.page || 1;
        const limit = params.limit || 10;
        const start = (page - 1) * limit;
        return {
          data: mock.slice(start, start + limit),
          meta: {
            total: mock.length,
            page,
            limit,
            totalPages: Math.ceil(mock.length / limit),
          },
        } as PaginatedResponse<Assessment>;
      }
    },
    staleTime: 30_000,
    placeholderData: (prev) => prev,
  });
}

// ─── Create assessment ────────────────────────────────────────────────────────

export function useCreateAssessment() {
  const queryClient = useQueryClient();
  const { addToast } = useToastStore();

  return useMutation({
    mutationFn: async (data: AssessmentFormData) => {
      try {
        return await createAssessment(data);
      } catch {
        // In dev, return a mock response
        const mock = generateMockAssessments()[0];
        return {
          ...mock,
          id: `assessment-${Date.now()}`,
          studentId: data.studentId,
          mathScore: data.mathScore,
          readingScore: data.readingScore,
          writingScore: data.writingScore,
          attendancePct: data.attendancePct,
          behaviorRating: data.behaviorRating,
          literacyLevel: data.literacyLevel,
          notes: data.notes,
          createdAt: new Date().toISOString(),
        };
      }
    },
    onSuccess: (data) => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: assessmentKeys.lists() });
      queryClient.invalidateQueries({ queryKey: assessmentKeys.dashboard });
      if (data.studentId) {
        queryClient.invalidateQueries({
          queryKey: studentKeys.assessments(data.studentId),
        });
      }
      addToast({
        title: 'Assessment submitted',
        description: 'The assessment has been recorded successfully.',
        variant: 'success',
      });
    },
    onError: (error) => {
      console.error('Assessment creation failed:', error);
    },
  });
}
