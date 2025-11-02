"use client";

import { useState, useEffect } from "react";
import { useUser } from '@auth0/nextjs-auth0';
import { useRouter } from 'next/navigation';
import Link from "next/link";
import { toast, Toaster } from "react-hot-toast";
import { speechApi } from "../../lib/api";

interface Speech {
  id: string;
  title: string;
  description: string;
  context: string;
  goal: string;
  with_context: boolean;
  completed: boolean;
  created_at: string;
  updated_at: string;
  session_count?: number;
  latest_session?: string;
}

export default function SpeechesPage() {
    console.log("Rendering SpeechesPage");
  const { user, isLoading } = useUser();
  const router = useRouter();
  const [speeches, setSpeeches] = useState<Speech[]>([]);
  const [loading, setLoading] = useState(true);

  // Redirect to login if not authenticated
  if (!isLoading && !user) {
    router.push('/auth/login');
    return <div>Redirecting to login...</div>;
  }

  useEffect(() => {
    if (user) {
        console.log("Authenticated user:", user);
      loadSpeeches();
    }
  }, [user]);

  const loadSpeeches = async () => {
    try {
      setLoading(true);
      const data = await speechApi.getSpeeches();
      console.log("Fetched speeches data:", data);
      setSpeeches(data.speeches || []);
    } catch (error) {
      console.error("Error loading speeches:", error);
      toast.error("Failed to load speeches");
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteSpeech = async (speechId: string, speechTitle: string) => {
    if (!confirm(`Are you sure you want to delete "${speechTitle}"? This action cannot be undone.`)) {
      return;
    }

    try {
      await speechApi.deleteSpeech(speechId);
      toast.success("Speech deleted successfully");
      loadSpeeches(); // Reload the list
    } catch (error) {
      console.error("Error deleting speech:", error);
      toast.error("Failed to delete speech");
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
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

  return (
    <div className="flex max-w-6xl mx-auto flex-col py-2 min-h-screen">
      <main className="flex flex-1 w-full flex-col px-4 mt-12 sm:mt-20">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl sm:text-5xl font-bold text-slate-900">
              My Speeches
            </h1>
            <p className="text-gray-600 mt-2">
              Manage your speeches and practice sessions
            </p>
          </div>
         <Link
              href="/speeches/new"
              className="bg-black text-white px-6 py-3 rounded-md font-medium hover:bg-gray-800 transition-colors"
            >
              + New Speech
            </Link>
        </div>

        {/* Navigation */}
        <div className="flex space-x-4 mb-6">
          <Link 
            href="/dashboard" 
            className="text-blue-600 hover:text-blue-800 font-medium"
          >
            ← Back to Dashboard
          </Link>
        </div>

        {/* Speeches List */}
        {speeches.length === 0 ? (
          <div className="text-center py-12">
            <div className="mb-4">
              <svg
                className="mx-auto h-12 w-12 text-gray-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No speeches yet
            </h3>
            <p className="text-gray-500 mb-6">
              Get started by creating your first speech to practice and improve your public speaking skills.
            </p>
            <Link
              href="/speeches/new"
              className="inline-flex items-center bg-black text-white px-4 py-2 rounded-md font-medium hover:bg-gray-800 transition-colors"
            >
              Create Your First Speech
            </Link>
          </div>
        ) : (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {speeches.map((speech) => (
              <div
                key={speech.id}
                className={`bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow ${
                  speech.completed ? 'ring-2 ring-green-200' : ''
                }`}
              >
                {/* Speech Header */}
                <div className="flex justify-between items-start mb-4">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">
                        {speech.title}
                      </h3>
                      {speech.completed && (
                        <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs font-medium">
                          ✓ Completed
                        </span>
                      )}
                    </div>
                    <div className="flex items-center space-x-2">
                      {speech.with_context && speech.context ? (
                        <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${getContextColor(speech.context)}`}>
                          {speech.context}
                        </span>
                      ) : (
                        <span className="bg-gray-100 text-gray-800 px-2 py-1 rounded-full text-xs font-medium">
                          Generic Speech
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Speech Content */}
                {speech.with_context ? (
                  <>
                    {speech.description && (
                      <p className="text-gray-600 text-sm mb-4 line-clamp-3">
                        {speech.description}
                      </p>
                    )}

                    {/* Speech Goal */}
                    {speech.goal && (
                      <div className="mb-4">
                        <p className="text-xs text-gray-500 mb-1">Goal:</p>
                        <p className="text-sm text-gray-700 line-clamp-2">
                          {speech.goal}
                        </p>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="mb-4">
                    <p className="text-sm text-gray-600 italic">
                      Generic speech created
                    </p>
                  </div>
                )}

                {/* Stats */}
                <div className="flex justify-between items-center text-sm text-gray-500 mb-4">
                  <span>{speech.session_count || 0} sessions</span>
                  <span>Created {formatDate(speech.created_at)}</span>
                </div>

                {/* Actions */}
                <div className="flex space-x-2">
                  <Link
                    href={`/speeches/${speech.id}`}
                    className="flex-1 bg-black text-white text-center py-2 px-3 rounded-md text-sm font-medium hover:bg-gray-800 transition-colors"
                  >
                    View Details
                  </Link>
                  <button
                    onClick={() => handleDeleteSpeech(speech.id, speech.title)}
                    className="bg-red-600 text-white py-2 px-3 rounded-md text-sm font-medium hover:bg-red-700 transition-colors"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
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
