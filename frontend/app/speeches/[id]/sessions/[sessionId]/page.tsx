"use client";

import { useState, useEffect } from "react";
import { useUser } from '@auth0/nextjs-auth0';
import { useRouter, useParams } from 'next/navigation';
import Link from "next/link";
import { toast, Toaster } from "react-hot-toast";
import { speechApi, sessionApi } from "../../../../../lib/api";
import ReactMarkdown from "react-markdown";
import dynamic from "next/dynamic";

// Dynamically import charts to avoid SSR issues
const FillerWordsChart = dynamic(() => import("../../../../../components/FillerWordsCharts"), { ssr: false });
const DeliveryMetricsTable = dynamic(() => import("../../../../../components/DeliveryMetrics"), { ssr: false });

interface Speech {
  id: string;
  title: string;
  description: string;
  context: string;
  goal: string;
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

export default function SessionDetailPage() {
  const { user, isLoading } = useUser();
  const router = useRouter();
  const params = useParams();
  const speechId = params.id as string;
  const sessionId = params.sessionId as string;
  
  const [speech, setSpeech] = useState<Speech | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  // Redirect to login if not authenticated
  if (!isLoading && !user) {
    router.push('/api/auth/login');
    return <div>Redirecting to login...</div>;
  }

  useEffect(() => {
    if (user && speechId && sessionId) {
      loadData();
    }
  }, [user, speechId, sessionId]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [speechData, sessionData] = await Promise.all([
        speechApi.getSpeech(speechId),
        sessionApi.getSession(sessionId)
      ]);
      
      setSpeech(speechData);
      setSession(sessionData);
    } catch (error) {
      console.error("Error loading data:", error);
      toast.error("Failed to load session data");
      router.push(`/speeches/${speechId}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteSession = async () => {
    if (!confirm("Are you sure you want to delete this session? This action cannot be undone.")) {
      return;
    }

    try {
      await sessionApi.deleteSession(sessionId);
      toast.success("Session deleted successfully");
      router.push(`/speeches/${speechId}`);
    } catch (error) {
      console.error("Error deleting session:", error);
      toast.error("Failed to delete session");
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

  const getFillerWordsData = () => {
    if (!session?.analysis_data?.filler_words) return null;
    
    const fillerWords = session.analysis_data.filler_words;
    const total = Object.values(fillerWords).reduce((sum: number, count: any) => sum + (count as number), 0);
    
    return {
      fillers: fillerWords,
      total
    };
  };

  const getDeliveryMetrics = () => {
    if (!session?.analysis_data) return null;
    
    return {
      duration: session.analysis_data.duration || 0,
      mean_intensity: session.analysis_data.mean_intensity || 0,
      mean_pitch: session.analysis_data.mean_pitch || 0,
      pitch_variation: session.analysis_data.pitch_variation || 0,
      word_count: session.analysis_data.word_count || 0,
      wpm: session.analysis_data.wpm || 0
    };
  };

  if (isLoading || loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  if (!speech || !session) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="text-lg">Session not found</div>
      </div>
    );
  }

  const fillerWordsData = getFillerWordsData();
  const deliveryMetrics = getDeliveryMetrics();

  return (
    <div className="flex max-w-4xl mx-auto flex-col py-2 min-h-screen">
      <main className="flex flex-1 w-full flex-col px-4 mt-12 sm:mt-20">
        {/* Navigation */}
        <div className="flex items-center space-x-4 mb-6">
          <Link 
            href={`/speeches/${speechId}`}
            className="text-blue-600 hover:text-blue-800 font-medium"
          >
            ← Back to Speech
          </Link>
        </div>

        {/* Session Header */}
        <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                {session.title || `Session from ${formatDate(session.created_at)}`}
              </h1>
              <p className="text-gray-600">
                For: <span className="font-medium">{speech.title}</span>
              </p>
            </div>
            <div className="flex space-x-3">
              <Link
                href={`/speeches/${speechId}/sessions/new`}
                className="bg-black text-white px-4 py-2 rounded-md font-medium hover:bg-gray-800"
              >
                New Session
              </Link>
              <button
                onClick={handleDeleteSession}
                className="bg-red-600 text-white px-4 py-2 rounded-md font-medium hover:bg-red-700"
              >
                Delete Session
              </button>
            </div>
          </div>
          
          <div className="text-sm text-gray-500">
            Recorded: {formatDate(session.created_at)}
            {session.filler_word_count !== undefined && (
              <span> • {session.filler_word_count} filler words detected</span>
            )}
          </div>
        </div>

        {/* Analysis Results */}
        <div className="space-y-6">
          {/* Scores Overview */}
          {session.scores && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Overall Scores</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(session.scores).map(([metric, score]) => (
                  <div key={metric} className="text-center">
                    <div className="text-2xl font-bold text-blue-600">
                      {typeof score === 'number' ? `${score}%` : String(score)}
                    </div>
                    <div className="text-sm text-gray-600 capitalize">
                      {metric.replace('_', ' ')}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Filler Words Chart */}
          {fillerWordsData && fillerWordsData.total > 0 && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Filler Words Analysis</h2>
              <FillerWordsChart fillerWords={fillerWordsData} />
            </div>
          )}

          {/* Delivery Metrics */}
          {deliveryMetrics && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Delivery Metrics</h2>
              <DeliveryMetricsTable metrics={deliveryMetrics} />
            </div>
          )}

          {/* Transcript */}
          {session.transcript && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Transcript</h2>
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                  {session.transcript}
                </p>
              </div>
            </div>
          )}

          {/* AI Feedback */}
          {session.feedback && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">AI Feedback & Recommendations</h2>
              <div className="prose max-w-none">
                {typeof session.feedback === 'string' ? (
                  <ReactMarkdown>{session.feedback}</ReactMarkdown>
                ) : (
                  <pre className="bg-gray-50 rounded-lg p-4 text-sm overflow-x-auto">
                    {JSON.stringify(session.feedback, null, 2)}
                  </pre>
                )}
              </div>
            </div>
          )}

          {/* Audio/Video Player */}
          {session.media_url && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Recording</h2>
              <div className="bg-gray-50 rounded-lg p-4">
                {session.media_url.includes('video') || session.media_url.includes('.mp4') || session.media_url.includes('.mov') ? (
                  <video 
                    controls 
                    className="w-full max-h-96 rounded-lg"
                    src={session.media_url}
                  >
                    Your browser does not support the video tag.
                  </video>
                ) : (
                  <audio 
                    controls 
                    className="w-full"
                    src={session.media_url}
                  >
                    Your browser does not support the audio tag.
                  </audio>
                )}
              </div>
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
