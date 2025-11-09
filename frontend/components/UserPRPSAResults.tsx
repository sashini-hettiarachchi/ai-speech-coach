"use client";

import { useState, useEffect } from "react";

interface PRPSAResult {
  id: number;
  assessment_type: string;
  total_score: number;
  anxiety_level: string;
  completed_at: string;
}

interface PRPSAComparison {
  initial: PRPSAResult;
  post_experimental: PRPSAResult;
  improvement: {
    score_change: number;
    percentage_change: number;
    anxiety_level_change: {
      from: string;
      to: string;
    };
    improved: boolean;
    interpretation: string;
  };
}

interface UserPRPSAResultsProps {
  onTakeAssessment: (type: 'initial' | 'post_experimental') => void;
}

export default function UserPRPSAResults({ onTakeAssessment }: UserPRPSAResultsProps) {
  const [assessments, setAssessments] = useState<Record<string, PRPSAResult>>({});
  const [comparison, setComparison] = useState<PRPSAComparison | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAssessments = async () => {
    try {
      setLoading(true);
      // Import the API utility dynamically to avoid SSR issues
      const { userPRPSAApi } = await import('../lib/api');
      
      const data = await userPRPSAApi.getAllAssessments();
      setAssessments(data.assessments);

      // If both assessments exist, fetch comparison
      if (data.completion_status.initial_completed && data.completion_status.post_experimental_completed) {
        fetchComparison();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const fetchComparison = async () => {
    try {
      // Import the API utility dynamically to avoid SSR issues
      const { userPRPSAApi } = await import('../lib/api');
      
      const data = await userPRPSAApi.getComparison();
      setComparison(data.comparison);
    } catch (err) {
      console.error('Failed to fetch comparison:', err);
    }
  };

  useEffect(() => {
    fetchAssessments();
  }, []);

  const getAnxietyLevelColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'low': return 'text-green-600 bg-green-100';
      case 'moderate': return 'text-yellow-600 bg-yellow-100';
      case 'high': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="text-gray-600 mt-4">Loading assessments...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="text-center text-red-600">
          <p>Error: {error}</p>
          <button
            onClick={fetchAssessments}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const hasInitial = 'initial' in assessments;
  const hasPostExperimental = 'post_experimental' in assessments;
  const canCompare = hasInitial && hasPostExperimental;

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          Public Speaking Anxiety Assessment Results
        </h1>
        <p className="text-gray-600 max-w-2xl mx-auto">
          Track your progress and see how your public speaking anxiety has changed over time.
        </p>
      </div>

      {/* Assessment Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {/* Initial Assessment Card */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Initial Assessment</h3>
            {hasInitial && (
              <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                Completed
              </span>
            )}
          </div>
          
          {hasInitial ? (
            <div className="space-y-3">
              <div>
                <p className="text-sm text-gray-600">PRPSA Score</p>
                <p className="text-2xl font-bold text-gray-900">{assessments.initial.total_score}</p>
                <p className="text-xs text-gray-500">Range: 34-170 (lower is better)</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-1">Anxiety Level</p>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getAnxietyLevelColor(assessments.initial.anxiety_level)}`}>
                  {assessments.initial.anxiety_level}
                </span>
              </div>
              <div>
                <p className="text-sm text-gray-600">Completed</p>
                <p className="text-sm text-gray-900">{formatDate(assessments.initial.completed_at)}</p>
              </div>
            </div>
          ) : (
            <div className="text-center">
              <p className="text-gray-500 mb-4">Take your initial assessment to establish a baseline for your public speaking anxiety.</p>
              <button
                onClick={() => onTakeAssessment('initial')}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                Take Initial Assessment
              </button>
            </div>
          )}
        </div>

        {/* Post-Experimental Assessment Card */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Post-Experimental Assessment</h3>
            {hasPostExperimental && (
              <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                Completed
              </span>
            )}
          </div>
          
          {hasPostExperimental ? (
            <div className="space-y-3">
              <div>
                <p className="text-sm text-gray-600">PRPSA Score</p>
                <p className="text-2xl font-bold text-gray-900">{assessments.post_experimental.total_score}</p>
                <p className="text-xs text-gray-500">Range: 34-170 (lower is better)</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 mb-1">Anxiety Level</p>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getAnxietyLevelColor(assessments.post_experimental.anxiety_level)}`}>
                  {assessments.post_experimental.anxiety_level}
                </span>
              </div>
              <div>
                <p className="text-sm text-gray-600">Completed</p>
                <p className="text-sm text-gray-900">{formatDate(assessments.post_experimental.completed_at)}</p>
              </div>
            </div>
          ) : (
            <div className="text-center">
              {hasInitial ? (
                <>
                  <p className="text-gray-500 mb-4">After practicing with the speech coach, take your post-experimental assessment to measure your progress.</p>
                  <button
                    onClick={() => onTakeAssessment('post_experimental')}
                    className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
                  >
                    Take Post-Experimental Assessment
                  </button>
                </>
              ) : (
                <p className="text-gray-500">Complete your initial assessment first</p>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Comparison Section */}
      {canCompare && comparison && (
        <div className="bg-white border border-gray-200 rounded-lg p-6 mb-8">
          <h3 className="text-xl font-semibold text-gray-900 mb-6">Progress Comparison</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Score Change */}
            <div className="text-center">
              <div className={`text-3xl font-bold mb-2 ${comparison.improvement.improved ? 'text-green-600' : comparison.improvement.score_change < 0 ? 'text-red-600' : 'text-gray-600'}`}>
                {comparison.improvement.score_change > 0 ? '-' : '+'}{Math.abs(comparison.improvement.score_change)}
              </div>
              <p className="text-sm text-gray-600">Score Change</p>
              <p className="text-xs text-gray-500 mt-1">
                {comparison.improvement.score_change > 0 ? 'Improvement' : comparison.improvement.score_change < 0 ? 'Increase' : 'No Change'}
              </p>
            </div>

            {/* Percentage Change */}
            <div className="text-center">
              <div className={`text-3xl font-bold mb-2 ${comparison.improvement.improved ? 'text-green-600' : comparison.improvement.percentage_change < 0 ? 'text-red-600' : 'text-gray-600'}`}>
                {comparison.improvement.percentage_change > 0 ? '-' : '+'}{Math.abs(comparison.improvement.percentage_change)}%
              </div>
              <p className="text-sm text-gray-600">Percentage Change</p>
              <p className="text-xs text-gray-500 mt-1">
                Relative to initial score
              </p>
            </div>

            {/* Anxiety Level Change */}
            <div className="text-center">
              <div className="flex justify-center items-center space-x-2 mb-2">
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${getAnxietyLevelColor(comparison.improvement.anxiety_level_change.from)}`}>
                  {comparison.improvement.anxiety_level_change.from}
                </span>
                <span className="text-gray-400">→</span>
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${getAnxietyLevelColor(comparison.improvement.anxiety_level_change.to)}`}>
                  {comparison.improvement.anxiety_level_change.to}
                </span>
              </div>
              <p className="text-sm text-gray-600">Anxiety Level</p>
              <p className="text-xs text-gray-500 mt-1">
                Before → After
              </p>
            </div>
          </div>

          <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h4 className="font-medium text-blue-900 mb-2">Interpretation</h4>
            <p className="text-sm text-blue-800">
              {comparison.improvement.interpretation}
            </p>
          </div>
        </div>
      )}

      {/* Information Section */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
        <h4 className="font-medium text-gray-900 mb-3">About PRPSA Scores</h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-600">
          <div>
            <h5 className="font-medium text-green-600 mb-1">Low Anxiety (34-97)</h5>
            <p>You have minimal public speaking anxiety and feel comfortable speaking in front of others.</p>
          </div>
          <div>
            <h5 className="font-medium text-yellow-600 mb-1">Moderate Anxiety (98-131)</h5>
            <p>You experience some nervousness about public speaking, which is normal for most people.</p>
          </div>
          <div>
            <h5 className="font-medium text-red-600 mb-1">High Anxiety (132-170)</h5>
            <p>You experience significant anxiety about public speaking and may benefit from practice and support.</p>
          </div>
        </div>
      </div>
    </div>
  );
}