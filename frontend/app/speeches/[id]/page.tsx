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

export default function SpeechDetailPage() {
  const { user, isLoading } = useUser();
  const router = useRouter();
  const params = useParams();
  const speechId = params.id as string;
  
  const [speech, setSpeech] = useState<Speech | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
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
    if (!confirm("Are you sure you want to mark this speech as completed? Once completed, you won't be able to create new speeches.")) {
      return;
    }

    try {
      const result = await speechApi.completeSpeech(speechId);
      setSpeech(result.speech);
      toast.success("Speech marked as completed!");
    } catch (error) {
      console.error("Error completing speech:", error);
      toast.error("Failed to complete speech");
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
    <div className="flex max-w-4xl mx-auto flex-col py-2 min-h-screen">
      <main className="flex flex-1 w-full flex-col px-4 mt-12 sm:mt-20">
        {/* Navigation */}
        <div className="flex items-center space-x-4 mb-6">
          <Link 
            href="/speeches" 
            className="text-blue-600 hover:text-blue-800 font-medium"
          >
            ← Back to Speeches
          </Link>
        </div>

        {/* Speech Details */}
        <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
          {isEditing ? (
            <form onSubmit={handleEditSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Title
                </label>
                <input
                  type="text"
                  value={editForm.title}
                  onChange={(e) => setEditForm(prev => ({ ...prev, title: e.target.value }))}
                  className="w-full rounded-md border-gray-300 shadow-sm focus:border-black focus:ring-black px-3 py-2"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  value={editForm.description}
                  onChange={(e) => setEditForm(prev => ({ ...prev, description: e.target.value }))}
                  rows={3}
                  className="w-full rounded-md border-gray-300 shadow-sm focus:border-black focus:ring-black px-3 py-2"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Context
                </label>
                <select
                  value={editForm.context}
                  onChange={(e) => setEditForm(prev => ({ ...prev, context: e.target.value }))}
                  className="w-full rounded-md border-gray-300 shadow-sm focus:border-black focus:ring-black px-3 py-2"
                >
                  {CONTEXT_OPTIONS.map(option => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Goal
                </label>
                <textarea
                  value={editForm.goal}
                  onChange={(e) => setEditForm(prev => ({ ...prev, goal: e.target.value }))}
                  rows={3}
                  className="w-full rounded-md border-gray-300 shadow-sm focus:border-black focus:ring-black px-3 py-2"
                  required
                />
              </div>
              
              <div className="flex space-x-3">
                <button
                  type="submit"
                  className="bg-black text-white px-4 py-2 rounded-md font-medium hover:bg-gray-800"
                >
                  Save Changes
                </button>
                <button
                  type="button"
                  onClick={() => setIsEditing(false)}
                  className="bg-gray-300 text-gray-700 px-4 py-2 rounded-md font-medium hover:bg-gray-400"
                >
                  Cancel
                </button>
              </div>
            </form>
          ) : (
            <>
              <div className="flex justify-between items-start mb-4">
                <div>
                  <div className="flex items-center space-x-3 mb-2">
                    <h1 className="text-3xl font-bold text-gray-900">
                      {speech.title}
                    </h1>
                    {speech.completed && (
                      <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-medium">
                        ✓ Completed
                      </span>
                    )}
                  </div>
                  <div className="flex items-center space-x-2">
                    {speech.with_context && speech.context && (
                      <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${getContextColor(speech.context)}`}>
                        {speech.context}
                      </span>
                    )}
                    {!speech.with_context && (
                      <span className="bg-gray-100 text-gray-800 px-3 py-1 rounded-full text-sm font-medium">
                        Generic Speech
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex space-x-2">
                  {!speech.completed && (
                    <button
                      onClick={() => setIsEditing(true)}
                      className="bg-gray-100 text-gray-700 px-4 py-2 rounded-md font-medium hover:bg-gray-200"
                    >
                      Edit Speech
                    </button>
                  )}
                </div>
              </div>
              
              {speech.with_context ? (
                <div className="space-y-4">
                  {speech.goal && (
                    <div>
                      <h3 className="text-sm font-medium text-gray-500 mb-1">Goal</h3>
                      <p className="text-gray-900">{speech.goal}</p>
                    </div>
                  )}
                  
                  {speech.audience_description && (
                    <div>
                      <h3 className="text-sm font-medium text-gray-500 mb-1">Audience</h3>
                      <p className="text-gray-900">{speech.audience_description}</p>
                    </div>
                  )}
                  
                  {speech.key_points && (
                    <div>
                      <h3 className="text-sm font-medium text-gray-500 mb-1">Key Points</h3>
                      <p className="text-gray-900 whitespace-pre-line">{speech.key_points}</p>
                    </div>
                  )}
                  
                  {speech.self_improvement_goal && (
                    <div>
                      <h3 className="text-sm font-medium text-gray-500 mb-1">Improvement Goals</h3>
                      <p className="text-gray-900">{speech.self_improvement_goal}</p>
                    </div>
                  )}
                  
                  {speech.description && (
                    <div>
                      <h3 className="text-sm font-medium text-gray-500 mb-1">Description</h3>
                      <p className="text-gray-900">{speech.description}</p>
                    </div>
                  )}
                  
                  <div className="text-sm text-gray-500">
                    Created: {formatDate(speech.created_at)}
                    {speech.updated_at !== speech.created_at && (
                      <span> • Updated: {formatDate(speech.updated_at)}</span>
                    )}
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h3 className="text-sm font-medium text-blue-900 mb-1">Generic Speech Mode</h3>
                    <p className="text-sm text-blue-700">
                      This is a Generic speech created with just a title. You can practice and get feedback without detailed context.
                    </p>
                  </div>
                  
                  <div className="text-sm text-gray-500">
                    Created: {formatDate(speech.created_at)}
                    {speech.updated_at !== speech.created_at && (
                      <span> • Updated: {formatDate(speech.updated_at)}</span>
                    )}
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Actions */}
        <div className="flex space-x-4 mb-6">
          {!speech.completed ? (
            <>
              <Link
                href={`/speeches/${speechId}/sessions/new`}
                className="bg-black text-white px-6 py-3 rounded-md font-medium hover:bg-gray-800 transition-colors"
              >
                + New Session
              </Link>
              <Link
                href={`/dashboard?speechId=${speechId}`}
                className="bg-gray-600 text-white px-6 py-3 rounded-md font-medium hover:bg-gray-700 transition-colors"
              >
                Quick Practice
              </Link>
              {sessions.length > 0 && (
                <button
                  onClick={handleCompleteSpeech}
                  className="bg-green-600 text-white px-6 py-3 rounded-md font-medium hover:bg-green-700 transition-colors"
                >
                  Mark as Complete
                </button>
              )}
            </>
          ) : (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 w-full">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-green-800">
                    Speech Completed!
                  </h3>
                  <div className="mt-1 text-sm text-green-700">
                    <p>This speech has been marked as completed. You can review sessions but cannot create new ones.</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Sessions List */}
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Practice Sessions ({sessions.length})
          </h2>
          
          {sessions.length === 0 ? (
            <div className="text-center py-8 bg-gray-50 rounded-lg">
              <p className="text-gray-500 mb-4">No practice sessions yet</p>
              <Link
                href={`/speeches/${speechId}/sessions/new`}
                className="inline-flex items-center bg-black text-white px-4 py-2 rounded-md font-medium hover:bg-gray-800"
              >
                Record Your First Session
              </Link>
            </div>
          ) : (
            <div className="space-y-4">
              {sessions.map((session) => (
                <div
                  key={session.id}
                  className="bg-white border border-gray-200 rounded-lg p-4"
                >
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <Link 
                        href={`/speeches/${speechId}/sessions/${session.id}`}
                        className="font-medium text-gray-900 hover:text-blue-600"
                      >
                        {session.title || `Session from ${formatDate(session.created_at)}`}
                      </Link>
                      {session.filler_word_count !== undefined && (
                        <p className="text-sm text-gray-500">
                          {session.filler_word_count} filler words detected
                        </p>
                      )}
                    </div>
                    <div className="flex space-x-2">
                      <Link
                        href={`/speeches/${speechId}/sessions/${session.id}`}
                        className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                      >
                        View Details
                      </Link>
                      <button
                        onClick={() => handleDeleteSession(session.id)}
                        className="text-red-600 hover:text-red-800 text-sm font-medium"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                  
                  {session.transcript && (
                    <div className="mb-3">
                      <h4 className="text-sm font-medium text-gray-700 mb-1">Transcript Preview</h4>
                      <p className="text-sm text-gray-600 line-clamp-2">
                        {session.transcript.substring(0, 150)}...
                      </p>
                    </div>
                  )}
                  
                  {session.feedback && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-1">Feedback Preview</h4>
                      <p className="text-sm text-gray-600 line-clamp-1">
                        {typeof session.feedback === 'string' 
                          ? session.feedback.substring(0, 100) + '...'
                          : 'Analysis completed'
                        }
                      </p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        <Toaster
          position="top-center"
          reverseOrder={false}
          toastOptions={{ duration: 3000 }}
        />
      </main>
    </div>
  );
}
