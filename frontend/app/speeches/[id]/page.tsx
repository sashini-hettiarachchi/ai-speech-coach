"use client";

import { useState, useEffect } from "react";
import { useUser } from '@auth0/nextjs-auth0';
import { useRouter, useParams } from 'next/navigation';
import Link from "next/link";
import { toast, Toaster } from "react-hot-toast";
import { speechApi, sessionApi } from "../../../lib/api";

interface Speech {
  id: string;
  title: string;
  description: string;
  context: string;
  goal: string;
  audience_description: string;
  key_points: string;
  self_improvement_goal: string;
  with_context: boolean;
  completed: boolean;
  prpsa_completed: boolean;
  created_at: string;
  updated_at: string;
}

interface Session {
  id: string;
  title?: string;
  transcript: string;
  feedback: string;
  filler_word_count: number;
  media_url: string;
  analysis_data: any;
  scores: any;
  created_at: string;
}

// Helper functions for session data processing
const getOverallScore = (scores: any) => {
  if (!scores || typeof scores !== 'object') return null;
  
  // Check for overall_score field
  if (scores.overall_score !== undefined) {
    return Math.round(scores.overall_score);
  }
  
  // Calculate from individual scores if available
  const scoreValues = Object.values(scores).filter((score): score is number => 
    typeof score === 'number' && score >= 0 && score <= 100
  );
  
  if (scoreValues.length > 0) {
    const average = scoreValues.reduce((sum: number, score: number) => sum + score, 0) / scoreValues.length;
    return Math.round(average);
  }
  
  return null;
};

const getFeedbackSummary = (feedback: any) => {
  if (!feedback) return null;
  
  // If feedback is a string, return first 100 characters
  if (typeof feedback === 'string') {
    return feedback.length > 100 ? feedback.substring(0, 100) + '...' : feedback;
  }
  
  // If feedback is an object, look for summary field
  if (typeof feedback === 'object') {
    if (feedback.summary) {
      const summary = feedback.summary;
      return summary.length > 100 ? summary.substring(0, 100) + '...' : summary;
    }
    
    // Look for other possible summary fields
    if (feedback.overall_feedback) {
      const summary = feedback.overall_feedback;
      return summary.length > 100 ? summary.substring(0, 100) + '...' : summary;
    }
    
    if (feedback.general_feedback) {
      const summary = feedback.general_feedback;
      return summary.length > 100 ? summary.substring(0, 100) + '...' : summary;
    }
  }
  
  return null;
};

const getScoreColor = (score: number) => {
  if (score >= 80) return 'text-green-600 bg-green-100';
  if (score >= 60) return 'text-yellow-600 bg-yellow-100';
  if (score >= 40) return 'text-orange-600 bg-orange-100';
  return 'text-red-600 bg-red-100';
};

export default function SpeechDetailPage() {
  const { user, isLoading } = useUser();
  const router = useRouter();
  const params = useParams();
  const speechId = params.id as string;
  
  const [speech, setSpeech] = useState<Speech | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCompletionModal, setShowCompletionModal] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({
    title: "",
    description: "",
    context: "Academic",
    goal: ""
  });

  const CONTEXT_OPTIONS = [
    { value: "Academic", label: "Academic" },
    { value: "Storytelling", label: "Storytelling" },
    { value: "Persuasive", label: "Persuasive" }
  ];

  // Redirect to login if not authenticated
  if (!isLoading && !user) {
    router.push('/api/auth/login');
    return <div>Redirecting to login...</div>;
  }

  useEffect(() => {
    if (user && speechId) {
      loadSpeechData();
    }
  }, [user, speechId]);

  // Check for showCompletion URL parameter
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('showCompletion') === 'true') {
      setShowCompletionModal(true);
    }
  }, []);

  const loadSpeechData = async () => {
    try {
      setLoading(true);
      const [speechData, sessionsData] = await Promise.all([
        speechApi.getSpeech(speechId),
        sessionApi.getSessions(speechId)
      ]);
      
      setSpeech(speechData);
      setSessions(sessionsData.sessions || []);
      
      // Initialize edit form with current data
      setEditForm({
        title: speechData.title,
        description: speechData.description,
        context: speechData.context,
        goal: speechData.goal
      });
    } catch (error) {
      console.error("Error loading speech data:", error);
      toast.error("Failed to load speech data");
      router.push('/speeches');
    } finally {
      setLoading(false);
    }
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const updatedSpeech = await speechApi.updateSpeech(speechId, editForm);
      setSpeech(updatedSpeech);
      setIsEditing(false);
      toast.success("Speech updated successfully!");
    } catch (error) {
      console.error("Error updating speech:", error);
      toast.error("Failed to update speech");
    }
  };

  const handleDeleteSession = async (sessionId: string) => {
    if (!confirm("Are you sure you want to delete this session? This action cannot be undone.")) {
      return;
    }

    try {
      await sessionApi.deleteSession(sessionId);
      toast.success("Session deleted successfully");
      loadSpeechData(); // Reload sessions
    } catch (error) {
      console.error("Error deleting session:", error);
      toast.error("Failed to delete session");
    }
  };

  const handleCompleteSpeech = async () => {
    // Check if PRPSA is completed
    if (!speech?.prpsa_completed) {
      setShowCompletionModal(true);
      return;
    }

    if (!confirm("Are you sure you want to mark this speech as completed? Once completed, you won't be able to create new sessions.")) {
      return;
    }

    try {
      const result = await speechApi.completeSpeech(speechId);
      setSpeech(result.speech);
      toast.success("Speech marked as completed!");
    } catch (error: any) {
      console.error("Error completing speech:", error);
      toast.error(error.response?.data?.error || "Failed to complete speech");
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getContextColor = (context: string) => {
    switch (context) {
      case 'Academic':
        return 'bg-blue-100 text-blue-800';
      case 'Storytelling':
        return 'bg-green-100 text-green-800';
      case 'Persuasive':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (isLoading || loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  if (!speech) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="text-lg">Speech not found</div>
      </div>
    );
  }

  return (
    <div className="flex max-w-6xl mx-auto flex-col py-2 min-h-screen bg-gray-50">
      <main className="flex flex-1 w-full flex-col px-4 mt-12 sm:mt-20">
        {/* Navigation */}
        <div className="flex items-center space-x-4 mb-8">
          <Link 
            href="/speeches" 
            className="inline-flex items-center text-blue-600 hover:text-blue-800 font-medium transition-colors duration-200"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Speeches
          </Link>
        </div>

        {/* Speech Details */}
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-8 mb-8">
          {isEditing ? (
            <div className="space-y-6">
              <div className="border-b border-gray-200 pb-4 mb-6">
                <h2 className="text-2xl font-bold text-gray-900">Edit Speech</h2>
                <p className="text-gray-600 mt-1">Update your speech details and preferences</p>
              </div>
              
              <form onSubmit={handleEditSubmit} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="md:col-span-2">
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Speech Title
                    </label>
                    <input
                      type="text"
                      value={editForm.title}
                      onChange={(e) => setEditForm(prev => ({ ...prev, title: e.target.value }))}
                      className="w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 px-4 py-3 text-lg"
                      placeholder="Enter speech title..."
                      required
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Speaking Context
                    </label>
                    <select
                      value={editForm.context}
                      onChange={(e) => setEditForm(prev => ({ ...prev, context: e.target.value }))}
                      className="w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 px-4 py-3"
                    >
                      {CONTEXT_OPTIONS.map(option => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Speech Goal
                    </label>
                    <textarea
                      value={editForm.goal}
                      onChange={(e) => setEditForm(prev => ({ ...prev, goal: e.target.value }))}
                      rows={4}
                      className="w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 px-4 py-3"
                      placeholder="What do you want to achieve with this speech?"
                      required
                    />
                  </div>
                  
                  <div className="md:col-span-2">
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Description
                    </label>
                    <textarea
                      value={editForm.description}
                      onChange={(e) => setEditForm(prev => ({ ...prev, description: e.target.value }))}
                      rows={4}
                      className="w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 px-4 py-3"
                      placeholder="Additional details about your speech..."
                      required
                    />
                  </div>
                </div>
                
                <div className="flex justify-end space-x-4 pt-6 border-t border-gray-200">
                  <button
                    type="button"
                    onClick={() => setIsEditing(false)}
                    className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors duration-200"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors duration-200"
                  >
                    Save Changes
                  </button>
                </div>
              </form>
            </div>
          ) : (
            <>
              <div className="flex justify-between items-start mb-6">
                <div className="flex-1">
                  <div className="flex items-center space-x-4 mb-4">
                    <h1 className="text-4xl font-bold text-gray-900 leading-tight">
                      {speech.title}
                    </h1>
                    <div className="flex items-center space-x-2">
                      {speech.completed && (
                        <span className="inline-flex items-center bg-green-100 text-green-800 px-3 py-1.5 rounded-full text-sm font-semibold">
                          <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                          Completed
                        </span>
                      )}
                      {!speech.completed && speech.prpsa_completed && (
                        <span className="inline-flex items-center bg-blue-100 text-blue-800 px-3 py-1.5 rounded-full text-sm font-semibold">
                          <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                          PRPSA Done
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {speech.with_context && speech.context && (
                      <span className={`inline-flex items-center px-3 py-1.5 rounded-full text-sm font-semibold ${getContextColor(speech.context)}`}>
                        <span className="w-2 h-2 bg-current rounded-full mr-2"></span>
                        {speech.context}
                      </span>
                    )}
                    {!speech.with_context && (
                      <span className="inline-flex items-center bg-gray-100 text-gray-800 px-3 py-1.5 rounded-full text-sm font-semibold">
                        <span className="w-2 h-2 bg-current rounded-full mr-2"></span>
                        Generic Speech
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex-shrink-0">
                  {!speech.completed && (
                    <button
                      onClick={() => setIsEditing(true)}
                      className="inline-flex items-center bg-gray-100 text-gray-700 px-4 py-2 rounded-lg font-medium hover:bg-gray-200 transition-colors duration-200"
                    >
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                      Edit Speech
                    </button>
                  )}
                </div>
              </div>
              
              {speech.with_context ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {speech.goal && (
                    <div className="bg-blue-50 rounded-lg p-4">
                      <div className="flex items-center mb-2">
                        <svg className="w-5 h-5 text-blue-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                        </svg>
                        <h3 className="text-sm font-semibold text-blue-900">Speech Goal</h3>
                      </div>
                      <p className="text-gray-800 leading-relaxed">{speech.goal}</p>
                    </div>
                  )}
                  
                  {speech.audience_description && (
                    <div className="bg-purple-50 rounded-lg p-4">
                      <div className="flex items-center mb-2">
                        <svg className="w-5 h-5 text-purple-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                        </svg>
                        <h3 className="text-sm font-semibold text-purple-900">Target Audience</h3>
                      </div>
                      <p className="text-gray-800 leading-relaxed">{speech.audience_description}</p>
                    </div>
                  )}
                  
                  {speech.key_points && (
                    <div className="bg-green-50 rounded-lg p-4 md:col-span-2">
                      <div className="flex items-center mb-2">
                        <svg className="w-5 h-5 text-green-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                        </svg>
                        <h3 className="text-sm font-semibold text-green-900">Key Points</h3>
                      </div>
                      <p className="text-gray-800 leading-relaxed whitespace-pre-line">{speech.key_points}</p>
                    </div>
                  )}
                  
                  {speech.self_improvement_goal && (
                    <div className="bg-orange-50 rounded-lg p-4">
                      <div className="flex items-center mb-2">
                        <svg className="w-5 h-5 text-orange-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                        <h3 className="text-sm font-semibold text-orange-900">Improvement Goals</h3>
                      </div>
                      <p className="text-gray-800 leading-relaxed">{speech.self_improvement_goal}</p>
                    </div>
                  )}
                  
                  {speech.description && (
                    <div className="bg-gray-50 rounded-lg p-4">
                      <div className="flex items-center mb-2">
                        <svg className="w-5 h-5 text-gray-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h7" />
                        </svg>
                        <h3 className="text-sm font-semibold text-gray-900">Description</h3>
                      </div>
                      <p className="text-gray-800 leading-relaxed">{speech.description}</p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="space-y-6">
                  <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6">
                    <div className="flex items-center mb-3">
                      <div className="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center mr-3">
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                        </svg>
                      </div>
                      <h3 className="text-lg font-semibold text-blue-900">Generic Speech Mode</h3>
                    </div>
                    <p className="text-blue-800 leading-relaxed">
                      This is a Generic speech created with just a title. You can practice and get feedback without detailed context requirements.
                    </p>
                  </div>
                </div>
              )}
              
              {/* Metadata */}
              <div className="mt-6 pt-6 border-t border-gray-200">
                <div className="flex items-center text-sm text-gray-500">
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Created {formatDate(speech.created_at)}
                  {speech.updated_at !== speech.created_at && (
                    <span className="ml-4 flex items-center">
                      <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      Updated {formatDate(speech.updated_at)}
                    </span>
                  )}
                </div>
              </div>
            </>
          )}
        </div>

        {/* Actions */}
        <div className="flex flex-wrap gap-4 mb-8">
          {!speech.completed ? (
            <>
              <Link
                href={`/speeches/${speechId}/sessions/new`}
                className="inline-flex items-center bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors duration-200 shadow-sm"
              >
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                New Session
              </Link>
              <Link
                href={`/dashboard?speechId=${speechId}`}
                className="inline-flex items-center bg-gray-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-gray-700 transition-colors duration-200 shadow-sm"
              >
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Quick Practice
              </Link>
              {sessions.length > 0 && (
                <button
                  onClick={handleCompleteSpeech}
                  className="inline-flex items-center bg-green-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-green-700 transition-colors duration-200 shadow-sm"
                >
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  {speech.prpsa_completed ? 'Mark as Complete' : 'Complete Speech (PRPSA Required)'}
                </button>
              )}
            </>
          ) : (
            <div className="bg-green-50 border border-green-200 rounded-xl p-6 w-full">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-10 h-10 bg-green-500 text-white rounded-full flex items-center justify-center">
                    <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  </div>
                </div>
                <div className="ml-4">
                  <h3 className="text-lg font-semibold text-green-800">
                    Speech Completed!
                  </h3>
                  <div className="mt-1 text-green-700">
                    <p>This speech has been marked as completed. You can review sessions but cannot create new ones.</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Sessions List */}
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">
                Practice Sessions
              </h2>
              <p className="text-gray-600 mt-1">
                {sessions.length} session{sessions.length !== 1 ? 's' : ''} recorded
              </p>
            </div>
            {sessions.length > 0 && !speech.completed && (
              <Link
                href={`/speeches/${speechId}/sessions/new`}
                className="inline-flex items-center bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors duration-200"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                Add Session
              </Link>
            )}
          </div>
          
          {sessions.length === 0 ? (
            <div className="text-center py-12 bg-gray-50 rounded-xl">
              <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No practice sessions yet</h3>
              <p className="text-gray-500 mb-6">Start practicing your speech and get AI-powered feedback</p>
              <Link
                href={`/speeches/${speechId}/sessions/new`}
                className="inline-flex items-center bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors duration-200"
              >
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
                Record Your First Session
              </Link>
            </div>
          ) : (
            <div className="space-y-4">
              {sessions.map((session, index) => (
                <div
                  key={session.id}
                  className="border border-gray-200 rounded-lg p-6 hover:border-blue-300 hover:shadow-sm transition-all duration-200"
                >
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <div className="w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-semibold">
                          {sessions.length - index}
                        </div>
                        <Link 
                          href={`/speeches/${speechId}/sessions/${session.id}`}
                          className="text-lg font-semibold text-gray-900 hover:text-blue-600 transition-colors duration-200"
                        >
                          {session.title || `Session from ${formatDate(session.created_at)}`}
                        </Link>
                      </div>
                      
                      <div className="flex items-center space-x-6 text-sm text-gray-600">
                        <div className="flex items-center">
                          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          {formatDate(session.created_at)}
                        </div>
                        {session.filler_word_count !== undefined && (
                          <div className="flex items-center">
                            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                            </svg>
                            {session.filler_word_count} filler words
                          </div>
                        )}
                        {(() => {
                          const overallScore = getOverallScore(session.scores);
                          return overallScore !== null && (
                            <div className="flex items-center">
                              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                              </svg>
                              <span className={`px-2 py-1 rounded-full text-xs font-semibold ${getScoreColor(overallScore)}`}>
                                {overallScore}% overall
                              </span>
                            </div>
                          );
                        })()}
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      <Link
                        href={`/speeches/${speechId}/sessions/${session.id}`}
                        className="inline-flex items-center text-blue-600 hover:text-blue-800 text-sm font-medium transition-colors duration-200"
                      >
                        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                        </svg>
                        View Details
                      </Link>
                      <button
                        onClick={() => handleDeleteSession(session.id)}
                        className="inline-flex items-center text-red-600 hover:text-red-800 text-sm font-medium transition-colors duration-200"
                      >
                        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                        Delete
                      </button>
                    </div>
                  </div>
                  
                  {/* Session Content Sections */}
                  <div className="space-y-3">
                    {session.transcript && (
                      <div className="bg-gray-50 rounded-lg p-3">
                        <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center">
                          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                          Transcript Preview
                        </h4>
                        <p className="text-sm text-gray-600 line-clamp-2 leading-relaxed">
                          {session.transcript.substring(0, 200)}...
                        </p>
                      </div>
                    )}
                    
                    {session.feedback && (
                      <div className="bg-blue-50 rounded-lg p-3">
                        <h4 className="text-sm font-semibold text-blue-900 mb-2 flex items-center">
                          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                          </svg>
                          AI Feedback Summary
                        </h4>
                        <p className="text-sm text-blue-800 leading-relaxed">
                          {(() => {
                            const summary = getFeedbackSummary(session.feedback);
                            return summary || 'Detailed analysis and recommendations available';
                          })()}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* PRPSA Completion Modal */}
        {showCompletionModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Complete PRPSA Assessment
              </h3>
              <div className="mb-6">
                {speech?.prpsa_completed ? (
                  <div className="text-green-600 mb-4">
                    <div className="flex items-center">
                      <svg className="h-5 w-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      PRPSA Assessment Completed
                    </div>
                  </div>
                ) : (
                  <div className="text-amber-600 mb-4">
                    <div className="flex items-center">
                      <svg className="h-5 w-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                      </svg>
                      PRPSA Assessment Required
                    </div>
                  </div>
                )}
                <p className="text-gray-600 mb-4">
                  {speech?.prpsa_completed 
                    ? "You have completed the PRPSA assessment and can now proceed to mark this speech as complete."
                    : "Before marking your speech as complete, you need to complete the Personal Report of Public Speaking Anxiety (PRPSA) assessment. This helps us understand your speaking experience and provide better recommendations."
                  }
                </p>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                  <p className="text-sm text-blue-700">
                    <strong>About PRPSA:</strong> The Personal Report of Public Speaking Anxiety is a 34-item questionnaire that measures communication apprehension specifically related to public speaking. It's a research-validated tool used to understand speaking anxiety levels.
                  </p>
                </div>
              </div>
              <div className="flex space-x-3">
                {speech?.prpsa_completed ? (
                  <>
                    <button
                      onClick={() => {
                        setShowCompletionModal(false);
                        handleCompleteSpeech();
                      }}
                      className="flex-1 bg-green-600 text-white px-4 py-2 rounded-md font-medium hover:bg-green-700"
                    >
                      Complete Speech
                    </button>
                    <button
                      onClick={() => setShowCompletionModal(false)}
                      className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md font-medium hover:bg-gray-400"
                    >
                      Cancel
                    </button>
                  </>
                ) : (
                  <>
                    <Link
                      href={`/speeches/${speechId}/prpsa`}
                      className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md font-medium hover:bg-blue-700 text-center"
                    >
                      Take PRPSA Assessment
                    </Link>
                    <button
                      onClick={() => setShowCompletionModal(false)}
                      className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md font-medium hover:bg-gray-400"
                    >
                      Cancel
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        )}

        <Toaster
          position="top-center"
          reverseOrder={false}
          toastOptions={{ duration: 3000 }}
        />
      </main>
    </div>
  );
}
