'use client';

import * as React from 'react';
import Link from 'next/link';
import {
  Search,
  Filter,
  TrendingUp,
  TrendingDown,
  Minus,
  ChevronLeft,
  ChevronRight,
  Eye,
} from 'lucide-react';
import { PageHeader } from '@/components/layout/PageHeader';
import { RiskBadge } from '@/components/shared/RiskBadge';
import { SkeletonRow } from '@/components/shared/LoadingSpinner';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useStudentsWithFilters } from '@/hooks/useStudents';
import { useStudentFilterStore } from '@/lib/store';
import { formatDate, getInitials, cn } from '@/lib/utils';
import type { RiskLevel } from '@/lib/types';

const GRADES = [
  'Grade 1',
  'Grade 2',
  'Grade 3',
  'Grade 4',
  'Grade 5',
  'Grade 6',
  'Grade 7',
  'Grade 8',
];

const RISK_LEVELS: Array<{ value: RiskLevel; label: string }> = [
  { value: 'low', label: 'Low Risk' },
  { value: 'medium', label: 'Medium Risk' },
  { value: 'high', label: 'High Risk' },
  { value: 'critical', label: 'Critical' },
];

const trendConfig = {
  improving: { icon: TrendingUp, color: 'text-success', label: 'Improving' },
  declining: { icon: TrendingDown, color: 'text-danger', label: 'Declining' },
  stable: { icon: Minus, color: 'text-text-secondary', label: 'Stable' },
};

export default function StudentsPage() {
  const { grade, riskLevel, search, page, setGrade, setRiskLevel, setSearch, setPage, resetFilters } =
    useStudentFilterStore();
  const { data, isLoading, isFetching } = useStudentsWithFilters();
  const [searchInput, setSearchInput] = React.useState(search);

  // Debounce search
  React.useEffect(() => {
    const timer = setTimeout(() => {
      setSearch(searchInput);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchInput, setSearch]);

  const students = data?.data || [];
  const meta = data?.meta;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Students"
        subtitle={
          meta ? `${meta.total} students enrolled` : 'Manage and monitor student records'
        }
      />

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            {/* Search */}
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-secondary" />
              <Input
                placeholder="Search students..."
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                className="pl-9"
              />
            </div>

            {/* Grade filter */}
            <Select
              value={grade || 'all'}
              onValueChange={(v) => setGrade(v === 'all' ? '' : v)}
            >
              <SelectTrigger className="w-full sm:w-[160px]">
                <SelectValue placeholder="All Grades" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Grades</SelectItem>
                {GRADES.map((g) => (
                  <SelectItem key={g} value={g}>
                    {g}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Risk level filter */}
            <Select
              value={riskLevel || 'all'}
              onValueChange={(v) => setRiskLevel(v === 'all' ? '' : v)}
            >
              <SelectTrigger className="w-full sm:w-[160px]">
                <SelectValue placeholder="All Risk Levels" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Risk Levels</SelectItem>
                {RISK_LEVELS.map((r) => (
                  <SelectItem key={r.value} value={r.value}>
                    {r.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Reset */}
            {(grade || riskLevel || search) && (
              <Button variant="ghost" size="sm" onClick={resetFilters}>
                Clear filters
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="divide-y">
              {[1, 2, 3, 4, 5].map((i) => (
                <SkeletonRow key={i} />
              ))}
            </div>
          ) : students.length > 0 ? (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="pl-6">Name</TableHead>
                    <TableHead>Grade</TableHead>
                    <TableHead>Last Assessment</TableHead>
                    <TableHead>Risk Level</TableHead>
                    <TableHead>Trend</TableHead>
                    <TableHead>Avg Score</TableHead>
                    <TableHead className="pr-6 text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {students.map((student) => {
                    const trend = student.trend ? trendConfig[student.trend] : null;
                    const TrendIcon = trend?.icon;
                    const avgScore =
                      student.averageMathScore !== undefined
                        ? Math.round(
                            ((student.averageMathScore || 0) +
                              (student.averageReadingScore || 0) +
                              (student.averageWritingScore || 0)) /
                              3
                          )
                        : null;

                    return (
                      <TableRow
                        key={student.id}
                        className={cn('cursor-pointer', isFetching && 'opacity-70')}
                      >
                        <TableCell className="pl-6">
                          <div className="flex items-center gap-3">
                            <div className="h-9 w-9 flex-shrink-0 rounded-full bg-primary flex items-center justify-center text-xs font-bold text-white">
                              {getInitials(student.name)}
                            </div>
                            <div>
                              <p className="font-medium text-text-primary">{student.name}</p>
                              {student.guardianName && (
                                <p className="text-xs text-text-secondary truncate max-w-[160px]">
                                  {student.guardianName}
                                </p>
                              )}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <span className="text-sm text-text-primary">{student.grade}</span>
                        </TableCell>
                        <TableCell>
                          <span className="text-sm text-text-secondary">
                            {student.lastAssessmentDate
                              ? formatDate(student.lastAssessmentDate)
                              : '—'}
                          </span>
                        </TableCell>
                        <TableCell>
                          {student.currentRiskLevel ? (
                            <RiskBadge level={student.currentRiskLevel as RiskLevel} size="sm" />
                          ) : (
                            <span className="text-xs text-text-secondary">No data</span>
                          )}
                        </TableCell>
                        <TableCell>
                          {trend && TrendIcon ? (
                            <span className={cn('flex items-center gap-1 text-xs font-medium', trend.color)}>
                              <TrendIcon className="h-3.5 w-3.5" />
                              {trend.label}
                            </span>
                          ) : (
                            <span className="text-xs text-text-secondary">—</span>
                          )}
                        </TableCell>
                        <TableCell>
                          {avgScore !== null ? (
                            <span
                              className={cn(
                                'font-semibold',
                                avgScore >= 75
                                  ? 'text-success'
                                  : avgScore >= 55
                                  ? 'text-warning'
                                  : 'text-danger'
                              )}
                            >
                              {avgScore}
                              <span className="text-xs text-text-secondary font-normal">/100</span>
                            </span>
                          ) : (
                            <span className="text-xs text-text-secondary">—</span>
                          )}
                        </TableCell>
                        <TableCell className="pr-6 text-right">
                          <Button asChild variant="ghost" size="sm">
                            <Link href={`/students/${student.id}`}>
                              <Eye className="h-4 w-4 mr-1" />
                              View
                            </Link>
                          </Button>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>

              {/* Pagination */}
              {meta && meta.totalPages > 1 && (
                <div className="flex items-center justify-between px-6 py-4 border-t border-gray-100">
                  <p className="text-sm text-text-secondary">
                    Showing {(meta.page - 1) * meta.limit + 1}–
                    {Math.min(meta.page * meta.limit, meta.total)} of {meta.total} students
                  </p>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage(page - 1)}
                      disabled={page <= 1}
                    >
                      <ChevronLeft className="h-4 w-4" />
                      Previous
                    </Button>
                    <span className="text-sm text-text-secondary px-2">
                      Page {meta.page} of {meta.totalPages}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage(page + 1)}
                      disabled={page >= meta.totalPages}
                    >
                      Next
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <div className="h-16 w-16 rounded-full bg-gray-100 flex items-center justify-center mb-4">
                <Search className="h-8 w-8 text-text-secondary" />
              </div>
              <h3 className="font-semibold text-text-primary mb-1">No students found</h3>
              <p className="text-sm text-text-secondary mb-4">
                Try adjusting your filters or search term
              </p>
              <Button variant="outline" size="sm" onClick={resetFilters}>
                Clear all filters
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
