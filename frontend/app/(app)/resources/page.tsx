'use client';

import * as React from 'react';
import {
  BookOpen,
  Calculator,
  Users,
  MessageCircle,
  Clock,
  Bookmark,
  BookmarkCheck,
  ExternalLink,
  Search,
} from 'lucide-react';
import { PageHeader } from '@/components/layout/PageHeader';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';
import type { Resource } from '@/lib/types';

const RESOURCES: Resource[] = [
  {
    id: '1',
    title: 'Phonics-Based Reading Intervention',
    description:
      'Structured phonics program designed for early readers struggling with decoding. Includes activities, flashcards, and assessment checkpoints.',
    category: 'reading',
    estimatedMinutes: 45,
    difficulty: 'beginner',
  },
  {
    id: '2',
    title: 'Guided Reading Groups Strategy',
    description:
      'Group students by reading level and implement targeted small-group instruction. Effective for mixed-ability classrooms common in African schools.',
    category: 'reading',
    estimatedMinutes: 60,
    difficulty: 'intermediate',
  },
  {
    id: '3',
    title: 'Repeated Reading Technique',
    description:
      'Research-backed method where students read the same text multiple times to build fluency, comprehension, and confidence.',
    category: 'reading',
    estimatedMinutes: 20,
    difficulty: 'beginner',
  },
  {
    id: '4',
    title: 'Concrete-Pictorial-Abstract Math',
    description:
      'Three-stage approach to teaching math concepts using physical objects, pictures, then abstract symbols. Highly effective for foundational math.',
    category: 'math',
    estimatedMinutes: 50,
    difficulty: 'intermediate',
  },
  {
    id: '5',
    title: 'Number Sense Activities',
    description:
      'Daily 10-minute activities to build number sense through games, mental math, and real-world problem solving.',
    category: 'math',
    estimatedMinutes: 10,
    difficulty: 'beginner',
  },
  {
    id: '6',
    title: 'Math Journals for Struggling Learners',
    description:
      'Structured journal prompts that help students articulate their mathematical thinking and identify misconceptions.',
    category: 'math',
    estimatedMinutes: 30,
    difficulty: 'intermediate',
  },
  {
    id: '7',
    title: 'Positive Behavior Support Framework',
    description:
      'School-wide framework for encouraging positive behaviors through consistent expectations, recognition, and gentle consequences.',
    category: 'behavior',
    estimatedMinutes: 90,
    difficulty: 'advanced',
  },
  {
    id: '8',
    title: 'Classroom Calm-Down Corner',
    description:
      'Setting up a designated space for emotional regulation. Includes tools, visual supports, and step-by-step instructions.',
    category: 'behavior',
    estimatedMinutes: 25,
    difficulty: 'beginner',
  },
  {
    id: '9',
    title: 'Restorative Practices Guide',
    description:
      'Moving beyond punitive discipline to restorative conversations that rebuild relationships and address root causes of behavior.',
    category: 'behavior',
    estimatedMinutes: 60,
    difficulty: 'intermediate',
  },
  {
    id: '10',
    title: 'Parent-Teacher Conference Preparation Kit',
    description:
      'Templates, talking points, and culturally sensitive approaches for productive conferences with families from diverse backgrounds.',
    category: 'parent',
    estimatedMinutes: 40,
    difficulty: 'beginner',
  },
  {
    id: '11',
    title: 'Family Engagement Strategies',
    description:
      'Evidence-based approaches to increase parent involvement, especially in communities where school-parent relationships are less established.',
    category: 'parent',
    estimatedMinutes: 55,
    difficulty: 'intermediate',
  },
  {
    id: '12',
    title: 'Supporting Learning at Home Guide',
    description:
      'Simple, practical activities that parents can do at home without formal education background. Available in multiple languages.',
    category: 'parent',
    estimatedMinutes: 20,
    difficulty: 'beginner',
  },
];

type CategoryFilter = 'all' | 'reading' | 'math' | 'behavior' | 'parent';

const CATEGORIES: Array<{ value: CategoryFilter; label: string; icon: React.ElementType; color: string }> = [
  { value: 'all', label: 'All Resources', icon: BookOpen, color: 'bg-gray-100 text-gray-700' },
  { value: 'reading', label: 'Reading Strategies', icon: BookOpen, color: 'bg-blue-100 text-blue-700' },
  { value: 'math', label: 'Math Interventions', icon: Calculator, color: 'bg-purple-100 text-purple-700' },
  { value: 'behavior', label: 'Behavior Management', icon: Users, color: 'bg-amber-100 text-amber-700' },
  { value: 'parent', label: 'Parent Communication', icon: MessageCircle, color: 'bg-emerald-100 text-emerald-700' },
];

const CATEGORY_ICON_MAP: Record<string, React.ElementType> = {
  reading: BookOpen,
  math: Calculator,
  behavior: Users,
  parent: MessageCircle,
};

const CATEGORY_COLOR_MAP: Record<string, string> = {
  reading: 'bg-blue-100 text-blue-700',
  math: 'bg-purple-100 text-purple-700',
  behavior: 'bg-amber-100 text-amber-700',
  parent: 'bg-emerald-100 text-emerald-700',
};

const DIFFICULTY_COLORS: Record<string, string> = {
  beginner: 'success',
  intermediate: 'warning',
  advanced: 'danger',
};

export default function ResourcesPage() {
  const [activeCategory, setActiveCategory] = React.useState<CategoryFilter>('all');
  const [search, setSearch] = React.useState('');
  const [saved, setSaved] = React.useState<Set<string>>(new Set());

  const filtered = RESOURCES.filter((r) => {
    const matchesCategory = activeCategory === 'all' || r.category === activeCategory;
    const matchesSearch =
      !search ||
      r.title.toLowerCase().includes(search.toLowerCase()) ||
      r.description.toLowerCase().includes(search.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  function toggleSave(id: string) {
    setSaved((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Resources"
        subtitle="Educational resources and teaching strategies"
      />

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-secondary" />
        <Input
          placeholder="Search resources..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-9 max-w-md"
        />
      </div>

      {/* Category filters */}
      <div className="flex flex-wrap gap-2">
        {CATEGORIES.map((cat) => {
          const Icon = cat.icon;
          return (
            <button
              key={cat.value}
              onClick={() => setActiveCategory(cat.value)}
              className={cn(
                'flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition-all',
                activeCategory === cat.value
                  ? 'bg-primary text-white shadow-sm'
                  : 'bg-white text-text-secondary border border-gray-200 hover:border-primary hover:text-primary'
              )}
            >
              <Icon className="h-4 w-4" />
              {cat.label}
              <span
                className={cn(
                  'text-xs rounded-full px-1.5',
                  activeCategory === cat.value ? 'bg-white/20 text-white' : 'bg-gray-100 text-text-secondary'
                )}
              >
                {cat.value === 'all'
                  ? RESOURCES.length
                  : RESOURCES.filter((r) => r.category === cat.value).length}
              </span>
            </button>
          );
        })}
      </div>

      {/* Results count */}
      <p className="text-sm text-text-secondary">
        Showing {filtered.length} resource{filtered.length !== 1 ? 's' : ''}
        {activeCategory !== 'all' && ` in ${CATEGORIES.find((c) => c.value === activeCategory)?.label}`}
        {search && ` matching "${search}"`}
      </p>

      {/* Resource grid */}
      {filtered.length > 0 ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {filtered.map((resource) => {
            const isSaved = saved.has(resource.id);
            const CategoryIcon = CATEGORY_ICON_MAP[resource.category] || BookOpen;
            const categoryColor = CATEGORY_COLOR_MAP[resource.category] || '';
            const difficultyVariant = (DIFFICULTY_COLORS[resource.difficulty] || 'secondary') as
              | 'success'
              | 'warning'
              | 'danger'
              | 'secondary';

            return (
              <Card
                key={resource.id}
                className="flex flex-col hover:shadow-md transition-shadow"
              >
                <CardContent className="flex flex-col h-full p-5">
                  {/* Header */}
                  <div className="flex items-start justify-between gap-2 mb-3">
                    <div
                      className={cn(
                        'flex items-center gap-1.5 text-xs font-medium rounded-full px-2.5 py-1',
                        categoryColor
                      )}
                    >
                      <CategoryIcon className="h-3.5 w-3.5" />
                      <span className="capitalize">{resource.category === 'parent' ? 'Parent Comm.' : resource.category}</span>
                    </div>
                    <button
                      onClick={() => toggleSave(resource.id)}
                      className={cn(
                        'rounded-lg p-1.5 transition-colors',
                        isSaved
                          ? 'text-primary bg-primary/10'
                          : 'text-text-secondary hover:bg-gray-100'
                      )}
                      aria-label={isSaved ? 'Remove from saved' : 'Save resource'}
                    >
                      {isSaved ? (
                        <BookmarkCheck className="h-4 w-4" />
                      ) : (
                        <Bookmark className="h-4 w-4" />
                      )}
                    </button>
                  </div>

                  {/* Content */}
                  <h3 className="font-semibold text-text-primary text-sm mb-2 leading-snug">
                    {resource.title}
                  </h3>
                  <p className="text-xs text-text-secondary leading-relaxed flex-1 mb-4">
                    {resource.description}
                  </p>

                  {/* Footer */}
                  <div className="flex items-center justify-between pt-3 border-t border-gray-100">
                    <div className="flex items-center gap-3">
                      <div className="flex items-center gap-1 text-xs text-text-secondary">
                        <Clock className="h-3.5 w-3.5" />
                        {resource.estimatedMinutes} min
                      </div>
                      <Badge variant={difficultyVariant} className="text-[10px]">
                        {resource.difficulty.charAt(0).toUpperCase() + resource.difficulty.slice(1)}
                      </Badge>
                    </div>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-primary hover:bg-primary/5 h-7 px-2 text-xs"
                    >
                      <ExternalLink className="h-3.5 w-3.5 mr-1" />
                      Open
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="h-16 w-16 rounded-full bg-gray-100 flex items-center justify-center mb-4">
            <Search className="h-8 w-8 text-text-secondary" />
          </div>
          <h3 className="font-semibold text-text-primary mb-1">No resources found</h3>
          <p className="text-sm text-text-secondary">
            Try adjusting your search or category filter
          </p>
          <Button
            variant="outline"
            size="sm"
            className="mt-4"
            onClick={() => {
              setSearch('');
              setActiveCategory('all');
            }}
          >
            Clear filters
          </Button>
        </div>
      )}
    </div>
  );
}
