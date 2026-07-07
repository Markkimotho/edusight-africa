import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  createInterventionFromSignal,
  generateMockAssessments,
  getSupportQueue,
  getSupportSummary,
} from '@/lib/api';
import type { SupportQueueItem, SupportSummary } from '@/lib/types';
import { useToastStore } from '@/lib/store';

const supportAll = ['support'] as const;

export const supportKeys = {
  all: supportAll,
  queue: (limit?: number) => [...supportAll, 'queue', limit] as const,
  summary: [...supportAll, 'summary'] as const,
};

function mockQueue(): SupportQueueItem[] {
  return generateMockAssessments().map((assessment) => ({
    studentId: assessment.studentId,
    studentName: assessment.studentName || assessment.studentId,
    gradeLevel: 6,
    schoolId: 'school-1',
    latestAssessmentId: assessment.id,
    latestAssessmentDate: assessment.createdAt.slice(0, 10),
    riskLevel: assessment.prediction?.riskLevel || 'medium',
    riskProbability: assessment.prediction?.riskProbability || 0.4,
    supportLevel:
      assessment.attendancePct < 70 || assessment.prediction?.riskLevel === 'critical'
        ? 'urgent'
        : assessment.attendancePct < 85 || assessment.prediction?.riskLevel === 'high'
          ? 'watch'
          : 'routine',
    confidence: 'medium',
    dataCompleteness: 0.75,
    attendancePct: assessment.attendancePct,
    academicAverage: Math.round((assessment.mathScore + assessment.readingScore + assessment.writingScore) / 3),
    literacyLevel: assessment.literacyLevel,
    riskDrivers: [],
    recommendedActions: [
      assessment.attendancePct < 85
        ? 'Guardian follow-up and weekly attendance target'
        : 'Teacher check-in and routine monitoring',
    ],
    openInterventions: 0,
    updatedAt: assessment.updatedAt,
  }));
}

export function useSupportQueue(limit = 25) {
  return useQuery({
    queryKey: supportKeys.queue(limit),
    queryFn: async () => {
      try {
        return await getSupportQueue({ limit });
      } catch {
        return mockQueue().slice(0, limit);
      }
    },
    staleTime: 30_000,
  });
}

export function useSupportSummary() {
  return useQuery({
    queryKey: supportKeys.summary,
    queryFn: async (): Promise<SupportSummary> => {
      try {
        return await getSupportSummary();
      } catch {
        const queue = mockQueue();
        return {
          totalStudents: queue.length,
          urgent: queue.filter((item) => item.supportLevel === 'urgent').length,
          watch: queue.filter((item) => item.supportLevel === 'watch').length,
          routine: queue.filter((item) => item.supportLevel === 'routine').length,
          openInterventions: 0,
          dataCompletenessAvg: 0.75,
        };
      }
    },
    staleTime: 30_000,
  });
}

export function useCreateInterventionFromSignal() {
  const queryClient = useQueryClient();
  const { addToast } = useToastStore();

  return useMutation({
    mutationFn: createInterventionFromSignal,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: supportKeys.all });
      addToast({
        title: 'Intervention planned',
        description: 'The support action has been added to the learner workflow.',
        variant: 'success',
      });
    },
  });
}
