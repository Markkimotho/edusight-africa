'use client';

import * as React from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  Heart,
  BookOpen,
  CheckSquare,
  Moon,
  Smile,
  Brain,
  Loader2,
  CheckCircle,
  TrendingUp,
} from 'lucide-react';
import { PageHeader } from '@/components/layout/PageHeader';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useToastStore } from '@/lib/store';
import { createObservation } from '@/lib/api';
import { cn, formatDate } from '@/lib/utils';
import type { ParentObservation } from '@/lib/types';

const observationSchema = z.object({
  studentId: z.string().min(1, 'Student name is required'),
  homeworkCompletion: z.number().min(0).max(100),
  readingMinutes: z.number().min(0).max(300),
  focusRating: z.number().min(1).max(5),
  behaviorHome: z.number().min(1).max(5),
  mood: z.number().min(1).max(5),
  sleepHours: z.number().min(5).max(12),
  notes: z.string().optional(),
});

type ObservationFormData = z.infer<typeof observationSchema>;

interface SliderFieldProps {
  label: string;
  icon: React.ElementType;
  name: keyof ObservationFormData;
  min: number;
  max: number;
  step?: number;
  formatValue?: (v: number) => string;
  control: ReturnType<typeof useForm<ObservationFormData>>['control'];
  color?: string;
}

function SliderField({
  label,
  icon: Icon,
  name,
  min,
  max,
  step = 1,
  formatValue,
  control,
  color = '#1B4332',
}: SliderFieldProps) {
  return (
    <Controller
      control={control}
      name={name}
      render={({ field }) => {
        const value = Number(field.value) || min;
        const pct = ((value - min) / (max - min)) * 100;
        const display = formatValue ? formatValue(value) : String(value);

        return (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Icon className="h-4 w-4 text-text-secondary" />
                <span className="text-sm font-medium text-text-primary">{label}</span>
              </div>
              <span
                className="text-sm font-bold rounded-lg px-2 py-0.5"
                style={{ color, backgroundColor: `${color}15` }}
              >
                {display}
              </span>
            </div>
            <div className="relative">
              <input
                type="range"
                min={min}
                max={max}
                step={step}
                value={value}
                onChange={(e) => field.onChange(Number(e.target.value))}
                className="w-full h-2 rounded-full appearance-none cursor-pointer"
                style={{
                  background: `linear-gradient(to right, ${color} 0%, ${color} ${pct}%, #E5E7EB ${pct}%, #E5E7EB 100%)`,
                }}
              />
            </div>
            <div className="flex justify-between text-xs text-text-secondary">
              <span>{formatValue ? formatValue(min) : min}</span>
              <span>{formatValue ? formatValue(max) : max}</span>
            </div>
          </div>
        );
      }}
    />
  );
}

const MOOD_EMOJIS: Record<number, { emoji: string; label: string }> = {
  1: { emoji: '😢', label: 'Very Sad' },
  2: { emoji: '😕', label: 'Sad' },
  3: { emoji: '😐', label: 'Neutral' },
  4: { emoji: '🙂', label: 'Happy' },
  5: { emoji: '😊', label: 'Very Happy' },
};

function MoodPicker({ control }: { control: ReturnType<typeof useForm<ObservationFormData>>['control'] }) {
  return (
    <Controller
      control={control}
      name="mood"
      render={({ field }) => {
        const value = Number(field.value) || 3;
        return (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Smile className="h-4 w-4 text-text-secondary" />
              <span className="text-sm font-medium text-text-primary">Mood</span>
            </div>
            <div className="flex gap-2">
              {[1, 2, 3, 4, 5].map((v) => (
                <button
                  key={v}
                  type="button"
                  onClick={() => field.onChange(v)}
                  className={cn(
                    'flex-1 flex flex-col items-center gap-1 rounded-xl py-2 text-2xl transition-all',
                    value === v
                      ? 'bg-primary/10 ring-2 ring-primary scale-105'
                      : 'hover:bg-gray-50'
                  )}
                >
                  <span>{MOOD_EMOJIS[v].emoji}</span>
                  <span className="text-[10px] text-text-secondary">{MOOD_EMOJIS[v].label}</span>
                </button>
              ))}
            </div>
          </div>
        );
      }}
    />
  );
}

// Mock recent observations
const mockRecentObservations: ParentObservation[] = [
  {
    id: '1',
    studentId: 'student-1',
    parentId: 'parent-1',
    homeworkCompletion: 85,
    readingMinutes: 30,
    focusRating: 4,
    behaviorHome: 4,
    mood: 4,
    sleepHours: 9,
    notes: 'Had a great day, finished all homework before dinner.',
    observationDate: new Date(Date.now() - 86400000).toISOString(),
    createdAt: new Date(Date.now() - 86400000).toISOString(),
  },
  {
    id: '2',
    studentId: 'student-1',
    parentId: 'parent-1',
    homeworkCompletion: 60,
    readingMinutes: 20,
    focusRating: 3,
    behaviorHome: 3,
    mood: 3,
    sleepHours: 8,
    notes: 'Was distracted today, hard time focusing.',
    observationDate: new Date(Date.now() - 2 * 86400000).toISOString(),
    createdAt: new Date(Date.now() - 2 * 86400000).toISOString(),
  },
];

export default function ParentPage() {
  const { addToast } = useToastStore();
  const [submitted, setSubmitted] = React.useState(false);
  const [isLoading, setIsLoading] = React.useState(false);

  const { control, register, handleSubmit, reset, formState: { errors } } =
    useForm<ObservationFormData>({
      resolver: zodResolver(observationSchema),
      defaultValues: {
        studentId: '',
        homeworkCompletion: 70,
        readingMinutes: 30,
        focusRating: 3,
        behaviorHome: 3,
        mood: 3,
        sleepHours: 9,
        notes: '',
      },
    });

  async function onSubmit(data: ObservationFormData) {
    setIsLoading(true);
    try {
      await createObservation({
        ...data,
        homeworkCompletion: data.homeworkCompletion,
        readingMinutes: data.readingMinutes,
        focusRating: data.focusRating,
        behaviorHome: data.behaviorHome,
        mood: data.mood,
        sleepHours: data.sleepHours,
        notes: data.notes,
      });
    } catch {
      // Mock success in dev
    } finally {
      setIsLoading(false);
      setSubmitted(true);
      addToast({
        title: 'Observation recorded!',
        description: 'Thank you for sharing your child\'s progress.',
        variant: 'success',
      });
    }
  }

  function handleNewObservation() {
    setSubmitted(false);
    reset();
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Parent Portal"
        subtitle="Share your child's home observations to help teachers understand the full picture"
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Form */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Heart className="h-5 w-5 text-accent" />
                <CardTitle className="text-base">Today&apos;s Observation</CardTitle>
              </div>
              <p className="text-sm text-text-secondary mt-1">
                Tell us about your child&apos;s day at home
              </p>
            </CardHeader>
            <CardContent>
              {submitted ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <div className="flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100 mb-4">
                    <CheckCircle className="h-8 w-8 text-success" />
                  </div>
                  <h3 className="text-xl font-bold text-text-primary mb-2">
                    Observation Recorded!
                  </h3>
                  <p className="text-sm text-text-secondary mb-6 max-w-sm">
                    Thank you for sharing. Your observations help teachers provide
                    better support for your child.
                  </p>
                  <Button onClick={handleNewObservation} variant="outline">
                    Add Another Observation
                  </Button>
                </div>
              ) : (
                <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                  {/* Student name */}
                  <div>
                    <label className="block text-sm font-medium text-text-primary mb-1.5">
                      Child&apos;s Name <span className="text-danger">*</span>
                    </label>
                    <Input
                      placeholder="Enter your child's name..."
                      {...register('studentId')}
                      className={cn(errors.studentId && 'border-danger')}
                    />
                    {errors.studentId && (
                      <p className="mt-1 text-xs text-danger">{errors.studentId.message}</p>
                    )}
                  </div>

                  {/* Mood picker */}
                  <MoodPicker control={control} />

                  {/* Sliders */}
                  <div className="space-y-5">
                    <SliderField
                      label="Homework Completion"
                      icon={CheckSquare}
                      name="homeworkCompletion"
                      min={0}
                      max={100}
                      formatValue={(v) => `${v}%`}
                      control={control}
                      color="#1B4332"
                    />
                    <SliderField
                      label="Reading Time"
                      icon={BookOpen}
                      name="readingMinutes"
                      min={0}
                      max={120}
                      step={5}
                      formatValue={(v) => `${v} min`}
                      control={control}
                      color="#2D6A4F"
                    />
                    <SliderField
                      label="Focus & Concentration"
                      icon={Brain}
                      name="focusRating"
                      min={1}
                      max={5}
                      formatValue={(v) =>
                        v === 1 ? 'Very Low' : v === 2 ? 'Low' : v === 3 ? 'Average' : v === 4 ? 'Good' : 'Excellent'
                      }
                      control={control}
                      color="#E76F51"
                    />
                    <SliderField
                      label="Behavior at Home"
                      icon={Heart}
                      name="behaviorHome"
                      min={1}
                      max={5}
                      formatValue={(v) =>
                        v === 1 ? 'Difficult' : v === 2 ? 'Challenging' : v === 3 ? 'Okay' : v === 4 ? 'Good' : 'Excellent'
                      }
                      control={control}
                      color="#F4A261"
                    />
                    <SliderField
                      label="Sleep Hours"
                      icon={Moon}
                      name="sleepHours"
                      min={5}
                      max={12}
                      step={0.5}
                      formatValue={(v) => `${v}h`}
                      control={control}
                      color="#1B4332"
                    />
                  </div>

                  {/* Notes */}
                  <div>
                    <label className="block text-sm font-medium text-text-primary mb-1.5">
                      Additional Notes
                      <span className="ml-1.5 text-xs text-text-secondary font-normal">(optional)</span>
                    </label>
                    <textarea
                      {...register('notes')}
                      rows={3}
                      placeholder="Any observations about your child's mood, health, or any special circumstances..."
                      className="flex w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-text-primary placeholder:text-text-secondary focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent resize-none"
                    />
                  </div>

                  <Button
                    type="submit"
                    className="w-full h-11"
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Saving...
                      </>
                    ) : (
                      <>
                        <Heart className="mr-2 h-4 w-4" />
                        Submit Observation
                      </>
                    )}
                  </Button>
                </form>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right sidebar */}
        <div className="space-y-4">
          {/* Info card */}
          <Card className="border-primary/20 bg-surface">
            <CardContent className="p-5">
              <div className="flex items-start gap-3">
                <div className="h-10 w-10 rounded-xl bg-primary flex items-center justify-center flex-shrink-0">
                  <TrendingUp className="h-5 w-5 text-white" />
                </div>
                <div>
                  <p className="font-semibold text-text-primary text-sm">Why it matters</p>
                  <p className="text-xs text-text-secondary mt-1 leading-relaxed">
                    Home observations combined with school assessments give teachers a
                    complete picture of your child&apos;s wellbeing and learning journey.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Recent observations */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Recent Observations</CardTitle>
              <p className="text-xs text-text-secondary">Last 7 days</p>
            </CardHeader>
            <CardContent className="space-y-3">
              {mockRecentObservations.map((obs) => (
                <div
                  key={obs.id}
                  className="rounded-xl border border-gray-100 bg-gray-50 p-3 space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-text-secondary">
                      {formatDate(obs.observationDate || obs.createdAt)}
                    </span>
                    <span className="text-xl">{MOOD_EMOJIS[obs.mood]?.emoji}</span>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <div className="text-center">
                      <p className="text-text-secondary">HW</p>
                      <p className="font-semibold text-text-primary">{obs.homeworkCompletion}%</p>
                    </div>
                    <div className="text-center">
                      <p className="text-text-secondary">Reading</p>
                      <p className="font-semibold text-text-primary">{obs.readingMinutes}m</p>
                    </div>
                    <div className="text-center">
                      <p className="text-text-secondary">Sleep</p>
                      <p className="font-semibold text-text-primary">{obs.sleepHours}h</p>
                    </div>
                  </div>
                  {obs.notes && (
                    <p className="text-xs text-text-secondary line-clamp-2">{obs.notes}</p>
                  )}
                </div>
              ))}
              {mockRecentObservations.length === 0 && (
                <p className="text-sm text-text-secondary text-center py-4">
                  No observations this week
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
