'use client';

import * as React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  ClipboardList,
  CheckCircle,
  AlertTriangle,
  Loader2,
  Info,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { PageHeader } from '@/components/layout/PageHeader';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { RiskBadge } from '@/components/shared/RiskBadge';
import { ScoreRadarChart } from '@/components/charts/ScoreRadarChart';
import { useCreateAssessment } from '@/hooks/useAssessments';
import { formatPercent, getFeatureLabel } from '@/lib/utils';
import { cn } from '@/lib/utils';
import type { Assessment, RiskLevel } from '@/lib/types';

const assessmentSchema = z.object({
  studentId: z.string().min(1, 'Student is required'),
  mathScore: z
    .number({ invalid_type_error: 'Required' })
    .min(0, 'Must be 0–100')
    .max(100, 'Must be 0–100'),
  readingScore: z
    .number({ invalid_type_error: 'Required' })
    .min(0, 'Must be 0–100')
    .max(100, 'Must be 0–100'),
  writingScore: z
    .number({ invalid_type_error: 'Required' })
    .min(0, 'Must be 0–100')
    .max(100, 'Must be 0–100'),
  attendancePct: z
    .number({ invalid_type_error: 'Required' })
    .min(0, 'Must be 0–100')
    .max(100, 'Must be 0–100'),
  behaviorRating: z
    .number({ invalid_type_error: 'Required' })
    .min(1, 'Must be 1–5')
    .max(5, 'Must be 1–5'),
  literacyLevel: z
    .number({ invalid_type_error: 'Required' })
    .min(1, 'Must be 1–10')
    .max(10, 'Must be 1–10'),
  notes: z.string().optional(),
});

type AssessmentFormData = z.infer<typeof assessmentSchema>;

interface ScoreInputProps {
  label: string;
  name: keyof AssessmentFormData;
  min: number;
  max: number;
  hint?: string;
  error?: string;
  register: ReturnType<typeof useForm<AssessmentFormData>>['register'];
}

function ScoreInput({ label, name, min, max, hint, error, register }: ScoreInputProps) {
  return (
    <div>
      <label className="block text-sm font-medium text-text-primary mb-1">
        {label}
        {hint && (
          <span className="ml-1.5 text-xs text-text-secondary font-normal">({hint})</span>
        )}
      </label>
      <Input
        type="number"
        min={min}
        max={max}
        placeholder={`${min}–${max}`}
        {...register(name, { valueAsNumber: true })}
        className={cn(error && 'border-danger focus:ring-danger')}
      />
      {error && <p className="mt-1 text-xs text-danger">{error}</p>}
    </div>
  );
}

export default function AssessPage() {
  const [result, setResult] = React.useState<Assessment | null>(null);
  const [studentName, setStudentName] = React.useState('');
  const [showDetails, setShowDetails] = React.useState(false);
  const createAssessment = useCreateAssessment();

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors },
  } = useForm<AssessmentFormData>({
    resolver: zodResolver(assessmentSchema),
    defaultValues: {
      studentId: '',
      mathScore: undefined,
      readingScore: undefined,
      writingScore: undefined,
      attendancePct: undefined,
      behaviorRating: undefined,
      literacyLevel: undefined,
      notes: '',
    },
  });

  const watchedValues = watch();

  async function onSubmit(data: AssessmentFormData) {
    try {
      const assessment = await createAssessment.mutateAsync(data);
      setResult(assessment);
      setStudentName(data.studentId);
    } catch (err) {
      console.error('Assessment submission failed:', err);
    }
  }

  function handleNewAssessment() {
    setResult(null);
    setStudentName('');
    reset();
  }

  const prediction = result?.prediction;
  const riskLevel = prediction?.riskLevel as RiskLevel | undefined;

  const riskColors: Record<RiskLevel, string> = {
    low: 'border-emerald-200 bg-emerald-50',
    medium: 'border-amber-200 bg-amber-50',
    high: 'border-orange-200 bg-orange-50',
    critical: 'border-red-200 bg-red-50',
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Student Assessment"
        subtitle="Record and analyze student performance with AI-powered risk prediction"
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
        {/* Form */}
        <Card className="lg:col-span-3">
          <CardHeader>
            <div className="flex items-center gap-2">
              <ClipboardList className="h-5 w-5 text-primary" />
              <CardTitle className="text-base">Assessment Form</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              {/* Student ID */}
              <div>
                <label className="block text-sm font-medium text-text-primary mb-1">
                  Student Name or ID <span className="text-danger">*</span>
                </label>
                <Input
                  placeholder="Search student name or enter ID..."
                  {...register('studentId')}
                  onChange={(e) => {
                    setStudentName(e.target.value);
                    register('studentId').onChange(e);
                  }}
                  className={cn(errors.studentId && 'border-danger')}
                />
                {errors.studentId && (
                  <p className="mt-1 text-xs text-danger">{errors.studentId.message}</p>
                )}
              </div>

              {/* Academic scores */}
              <div>
                <h3 className="text-sm font-semibold text-text-primary mb-3 flex items-center gap-2">
                  <span className="h-5 w-5 rounded-full bg-primary/10 flex items-center justify-center text-xs text-primary font-bold">1</span>
                  Academic Scores
                </h3>
                <div className="grid grid-cols-3 gap-4">
                  <ScoreInput
                    label="Math Score"
                    name="mathScore"
                    min={0}
                    max={100}
                    hint="0–100"
                    error={errors.mathScore?.message}
                    register={register}
                  />
                  <ScoreInput
                    label="Reading Score"
                    name="readingScore"
                    min={0}
                    max={100}
                    hint="0–100"
                    error={errors.readingScore?.message}
                    register={register}
                  />
                  <ScoreInput
                    label="Writing Score"
                    name="writingScore"
                    min={0}
                    max={100}
                    hint="0–100"
                    error={errors.writingScore?.message}
                    register={register}
                  />
                </div>
              </div>

              {/* Behavioral metrics */}
              <div>
                <h3 className="text-sm font-semibold text-text-primary mb-3 flex items-center gap-2">
                  <span className="h-5 w-5 rounded-full bg-primary/10 flex items-center justify-center text-xs text-primary font-bold">2</span>
                  Behavioral & Attendance Metrics
                </h3>
                <div className="grid grid-cols-3 gap-4">
                  <ScoreInput
                    label="Attendance"
                    name="attendancePct"
                    min={0}
                    max={100}
                    hint="% present"
                    error={errors.attendancePct?.message}
                    register={register}
                  />
                  <ScoreInput
                    label="Behavior Rating"
                    name="behaviorRating"
                    min={1}
                    max={5}
                    hint="1–5"
                    error={errors.behaviorRating?.message}
                    register={register}
                  />
                  <ScoreInput
                    label="Literacy Level"
                    name="literacyLevel"
                    min={1}
                    max={10}
                    hint="1–10"
                    error={errors.literacyLevel?.message}
                    register={register}
                  />
                </div>
              </div>

              {/* Notes */}
              <div>
                <label className="block text-sm font-medium text-text-primary mb-1">
                  Additional Notes
                  <span className="ml-1.5 text-xs text-text-secondary font-normal">(optional)</span>
                </label>
                <textarea
                  {...register('notes')}
                  rows={3}
                  placeholder="Optional observations about this student's behavior, learning style, or home situation..."
                  className="flex w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-text-primary placeholder:text-text-secondary focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent resize-none"
                />
              </div>

              <div className="flex gap-3">
                <Button
                  type="submit"
                  className="flex-1"
                  disabled={createAssessment.isPending}
                >
                  {createAssessment.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    'Submit Assessment'
                  )}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleNewAssessment}
                  disabled={createAssessment.isPending}
                >
                  Reset
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Right column: Radar + Result */}
        <div className="lg:col-span-2 space-y-4">
          {/* Radar chart preview */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Performance Radar</CardTitle>
              <p className="text-xs text-text-secondary">
                Live preview of entered scores vs healthy baseline
              </p>
            </CardHeader>
            <CardContent>
              <ScoreRadarChart
                mathScore={watchedValues.mathScore || 0}
                readingScore={watchedValues.readingScore || 0}
                writingScore={watchedValues.writingScore || 0}
                attendancePct={watchedValues.attendancePct || 0}
                behaviorRating={watchedValues.behaviorRating || 0}
                literacyLevel={watchedValues.literacyLevel || 0}
                height={260}
              />
            </CardContent>
          </Card>

          {/* Prediction result */}
          {result && prediction && riskLevel && (
            <Card className={cn('border-2', riskColors[riskLevel])}>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {riskLevel === 'low' ? (
                      <CheckCircle className="h-5 w-5 text-success" />
                    ) : (
                      <AlertTriangle className="h-5 w-5 text-warning" />
                    )}
                    <CardTitle className="text-base">Prediction Result</CardTitle>
                  </div>
                  <RiskBadge level={riskLevel} size="md" />
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Student + probability */}
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-xs text-text-secondary">Student</p>
                    <p className="font-semibold text-text-primary">{studentName}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-text-secondary">Risk Probability</p>
                    <p className="text-2xl font-bold text-text-primary">
                      {formatPercent((prediction.riskProbability || 0) * 100, 0)}
                    </p>
                  </div>
                </div>

                {/* Confidence */}
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-text-secondary">Model Confidence</span>
                    <span className="font-medium">{formatPercent((prediction.confidence || 0) * 100, 0)}</span>
                  </div>
                  <div className="h-2 w-full rounded-full bg-white/50 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-primary transition-all"
                      style={{ width: `${(prediction.confidence || 0) * 100}%` }}
                    />
                  </div>
                </div>

                {/* Top contributing factors */}
                {prediction.featureImportances && prediction.featureImportances.length > 0 && (
                  <div>
                    <button
                      onClick={() => setShowDetails((v) => !v)}
                      className="flex w-full items-center justify-between text-xs font-semibold text-text-primary mb-2 hover:text-primary transition-colors"
                    >
                      <span>Top Contributing Factors</span>
                      {showDetails ? (
                        <ChevronUp className="h-4 w-4" />
                      ) : (
                        <ChevronDown className="h-4 w-4" />
                      )}
                    </button>
                    {showDetails && (
                      <div className="space-y-2">
                        {prediction.featureImportances.slice(0, 4).map((fi) => (
                          <div key={fi.feature}>
                            <div className="flex justify-between text-xs mb-1">
                              <span className="text-text-secondary">
                                {getFeatureLabel(fi.feature)}
                              </span>
                              <span className="font-medium text-text-primary">
                                {formatPercent(fi.importance * 100, 0)} importance
                              </span>
                            </div>
                            <div className="h-1.5 w-full rounded-full bg-gray-200 overflow-hidden">
                              <div
                                className="h-full rounded-full bg-accent"
                                style={{ width: `${fi.importance * 100}%` }}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Interventions */}
                {prediction.recommendedInterventions && prediction.recommendedInterventions.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-text-primary mb-2">
                      Recommended Interventions
                    </p>
                    <ul className="space-y-1">
                      {prediction.recommendedInterventions.map((intervention, i) => (
                        <li key={i} className="flex items-start gap-2 text-xs text-text-secondary">
                          <span className="mt-0.5 h-1.5 w-1.5 rounded-full bg-accent flex-shrink-0" />
                          {intervention}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <Button
                  onClick={handleNewAssessment}
                  variant="outline"
                  size="sm"
                  className="w-full"
                >
                  Assess Another Student
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Info box when no result */}
          {!result && (
            <div className="rounded-xl border border-blue-200 bg-blue-50 p-4">
              <div className="flex items-start gap-3">
                <Info className="h-4 w-4 text-blue-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-semibold text-blue-900">How it works</p>
                  <p className="text-xs text-blue-700 mt-1">
                    Fill in the student&apos;s scores and our ML model will predict their risk level
                    and suggest targeted interventions.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
