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
const MediaPlayer = dynamic(() => import("../../../../../components/MediaPlayer"), { ssr: false });

// Dynamic imports for recharts
const BarChart = dynamic(() => import('recharts').then(mod => mod.BarChart), { ssr: false });
const Bar = dynamic(() => import('recharts').then(mod => mod.Bar), { ssr: false });
const LineChart = dynamic(() => import('recharts').then(mod => mod.LineChart), { ssr: false });
const Line = dynamic(() => import('recharts').then(mod => mod.Line), { ssr: false });
const XAxis = dynamic(() => import('recharts').then(mod => mod.XAxis), { ssr: false });
const YAxis = dynamic(() => import('recharts').then(mod => mod.YAxis), { ssr: false });
const CartesianGrid = dynamic(() => import('recharts').then(mod => mod.CartesianGrid), { ssr: false });
const Tooltip = dynamic(() => import('recharts').then(mod => mod.Tooltip), { ssr: false });
const ResponsiveContainer = dynamic(() => import('recharts').then(mod => mod.ResponsiveContainer), { ssr: false });

interface Speech {
    id: string;
    title: string;
    description: string;
    context: string;
    goal: string;
}

interface PauseEvent {
    start_time: number;
    end_time: number;
    duration: number;
    pause_type: string;
}

interface PitchEvent {
    start_time: number;
    end_time: number;
    pitch_type: string;
    relative_change: number;
    standard_deviation: number;
}

interface SpeedEvent {
    start_time: number;
    end_time: number;
    speed_type: string;
    relative_change: number;
    standard_deviation: number;
}

interface VolumeEvent {
    start_time: number;
    end_time: number;
    volume_type: string;
    relative_change: number;
    standard_deviation: number;
}

interface Session {
    id: string;
    title?: string;
    transcript: string;
    feedback: string;
    filler_word_count: number;
    filler_word_percentage: number;
    media_url: string;
    media_type: string;
    original_filename: string;
    created_at: string;
    duration_seconds: number;
    words_per_minute: number;
    syllables_per_minute: number;
    pitch_mean: number;
    pitch_std: number;
    volume_mean: number;
    volume_std: number;
    pause_events: PauseEvent[];
    pitch_events: PitchEvent[];
    speed_events: SpeedEvent[];
    volume_events: VolumeEvent[];
    filler_word_details: {
        fillers: Record<string, number>;
        total_fillers: number;
        filler_percentage: number;
        word_count: number;
    };
    full_analysis_results?: {
        feedback?: {
            cssef_evaluation?: Record<string, any>;
            micro_exercises?: Array<{
                title: string;
                description: string;
                duration: string;
                focus_area: string;
            }>;
            suggestions?: string[];
            summary?: string;
            motivation?: string;
            context_specific_tips?: string[];
            improved_excerpt?: string;
            strengths?: Array<{
                title: string;
                details?: string;
                evidence?: string;
                criterion?: string;
            }>;
            issues?: Array<{
                title: string;
                details?: string;
                evidence?: string;
                criterion?: string;
            }>;
        };
        feedback_without_context?: {
            cssef_evaluation?: Record<string, any>;
            micro_exercises?: Array<{
                title: string;
                description: string;
                duration: string;
                focus_area: string;
            }>;
            suggestions?: string[];
            summary?: string;
            motivation?: string;
            improved_excerpt?: string;
            strengths?: Array<{
                title: string;
                details?: string;
                evidence?: string;
                criterion?: string;
            }>;
            issues?: Array<{
                title: string;
                details?: string;
                evidence?: string;
                criterion?: string;
            }>;
        } | string;
    };
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
    const [userSelfRating, setUserSelfRating] = useState<any>(null);

    // Handle media URL refresh
    const handleMediaUrlRefresh = (newUrl: string) => {
        if (session) {
            setSession({ ...session, media_url: newUrl });
        }
    };

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
            
            // Load session data
            const sessionData = await sessionApi.getSession(sessionId);
            setSession(sessionData);
            
            // Load speech data
            const speechData = await speechApi.getSpeech(params.id as string);
            setSpeech(speechData);
            
            // Load user self-rating if it exists
            if (sessionData?.user_self_rating) {
                setUserSelfRating(sessionData.user_self_rating);
            } else {
                // Try to fetch self-rating separately
                try {
                    const selfRatingData = await sessionApi.getSelfRating(sessionId);
                    setUserSelfRating(selfRatingData?.self_rating);
                } catch (error) {
                    // Self-rating doesn't exist, that's okay
                    setUserSelfRating(null);
                }
            }
            
        } catch (error) {
            console.error("Error loading session data:", error);
            toast.error("Failed to load session data");
        } finally {
            setLoading(false);
        }
    };    const handleDeleteSession = async () => {
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

    const formatDuration = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    // Prepare data for pause events timeline
    const getPauseTimelineData = () => {
        if (!session?.pause_events) return [];

        return session.pause_events.map((pause, index) => ({
            name: `${Math.round(pause.start_time)}s`,
            time: pause.start_time,
            Duration: pause.duration,
            type: pause.pause_type,
            end: pause.end_time,
            // Add a formatted label for better display
            label: `${pause.pause_type} (${pause.duration.toFixed(1)}s)`
        }));
    };

    // Prepare data for speed events chart
    const getSpeedEventsData = () => {
        if (!session?.speed_events) return [];

        return session.speed_events.map((event, index) => ({
            name: `${Math.round(event.start_time)}s`,
            time: event.start_time,
            speed: event.relative_change,
            type: event.speed_type,
            'Speed Multiplier': event.relative_change
        }));
    };

    // Prepare data for pitch events chart
    const getPitchEventsData = () => {
        if (!session?.pitch_events) return [];

        return session.pitch_events.map((event, index) => ({
            name: `${Math.round(event.start_time)}s`,
            time: event.start_time,
            change: event.relative_change,
            type: event.pitch_type,
            'Pitch Change': event.relative_change
        }));
    };

    // Get CSSEF scores for display
    const getCSSEFScores = () => {
        if (!session?.full_analysis_results?.feedback?.cssef_evaluation) return null;

        const evaluation = session.full_analysis_results.feedback.cssef_evaluation;
        return Object.entries(evaluation).map(([key, value]: [string, any]) => ({
            criterion: key.replace('C', '').replace('_', ' ').replace(/\d+/, '').trim(),
            score: value.score || 0,
            strengths: value.strengths || [],
            improvements: value.improvements || []
        }));
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

    const pauseTimelineData = getPauseTimelineData();
    const speedEventsData = getSpeedEventsData();
    const pitchEventsData = getPitchEventsData();
    const cssefScores = getCSSEFScores();

    console.log("session", session)

    return (
        <div className="flex max-w-6xl mx-auto flex-col py-2 min-h-screen">
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

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                        <div className="text-center">
                            <div className="text-2xl font-bold text-blue-600">{formatDuration(session.duration_seconds)}</div>
                            <div className="text-sm text-gray-600">Duration</div>
                        </div>
                        <div className="text-center">
                            <div className="text-2xl font-bold text-green-600">{Math.round(session.words_per_minute)}</div>
                            <div className="text-sm text-gray-600">Words/min</div>
                        </div>
                        <div className="text-center">
                            <div className="text-2xl font-bold text-orange-600">{session.filler_word_count}</div>
                            <div className="text-sm text-gray-600">Filler Words</div>
                        </div>
                        <div className="text-center">
                            <div className="text-2xl font-bold text-red-600">{session.filler_word_percentage.toFixed(1)}%</div>
                            <div className="text-sm text-gray-600">Filler Rate</div>
                        </div>
                    </div>
                </div>

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

              
                {/* ANALYSIS SECTION */}
                <div className="bg-gradient-to-r from-gray-50 to-slate-50 border border-gray-200 rounded-lg p-4 mb-6 mt-6">
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center">
                        <span className="w-8 h-8 bg-gray-700 text-white rounded-full flex items-center justify-center text-sm mr-3">📊</span>
                        Speech Analysis
                    </h1>
                    <p className="text-gray-600 text-sm mt-2">Detailed metrics and visualizations of your speech performance</p>
                </div>

                {/* Analysis Results */}
                <div className="space-y-6">
                      {/* Filler Words Analysis */}
                {session.filler_word_details && (
                    <div className="bg-white border border-gray-200 rounded-lg p-4">
                        <h2 className="text-lg font-bold text-gray-900 mb-3">Filler Words Analysis</h2>
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="border-b border-gray-200">
                                        <th className="text-left py-2 px-3 font-medium text-gray-700">Filler Word</th>
                                        <th className="text-center py-2 px-3 font-medium text-gray-700">Count</th>
                                        <th className="text-center py-2 px-3 font-medium text-gray-700">Percentage</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {Object.entries(session.filler_word_details.fillers).map(([word, count]) => {
                                        const percentage = ((count / session.filler_word_details.total_fillers) * 100).toFixed(1);
                                        return (
                                            <tr key={word} className="border-b border-gray-100 hover:bg-gray-50">
                                                <td className="py-2 px-3 font-medium text-gray-900">"{word}"</td>
                                                <td className="py-2 px-3 text-center text-orange-600 font-bold">{count}</td>
                                                <td className="py-2 px-3 text-center text-gray-600">{percentage}%</td>
                                            </tr>
                                        );
                                    })}
                                    <tr className="border-t-2 border-gray-300 bg-gray-50">
                                        <td className="py-2 px-3 font-bold text-gray-900">Total</td>
                                        <td className="py-2 px-3 text-center font-bold text-red-600">{session.filler_word_details.total_fillers}</td>
                                        <td className="py-2 px-3 text-center font-bold text-red-600">{session.filler_word_details.filler_percentage.toFixed(1)}%</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
                  
                    {/* Prosody Overview */}
                    <div className="bg-white border border-gray-200 rounded-lg p-6">
                        <h2 className="text-xl font-bold text-gray-900 mb-4">Prosody Overview</h2>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                            <div className="text-center">
                                <div className="text-3xl font-bold text-purple-600">{Math.round(session.pitch_mean)}</div>
                                <div className="text-sm text-gray-600">Mean Pitch (Hz)</div>
                                <div className="text-xs text-gray-500">±{Math.round(session.pitch_std)}</div>
                            </div>
                            <div className="text-center">
                                <div className="text-3xl font-bold text-indigo-600">{Math.round(session.volume_mean)}</div>
                                <div className="text-sm text-gray-600">Mean Volume (dB)</div>
                                <div className="text-xs text-gray-500">±{Math.round(session.volume_std)}</div>
                            </div>
                            <div className="text-center">
                                <div className="text-3xl font-bold text-cyan-600">{session.pause_events.length}</div>
                                <div className="text-sm text-gray-600">Pause Events</div>
                            </div>
                            <div className="text-center">
                                <div className="text-3xl font-bold text-teal-600">{session.speed_events.length}</div>
                                <div className="text-sm text-gray-600">Speed Variations</div>
                            </div>
                        </div>
                    </div>

                    {/* Speed Events Chart */}
                    {speedEventsData.length > 0 && (
                        <div className="bg-white border border-gray-200 rounded-lg p-6">
                            <h2 className="text-xl font-bold text-gray-900 mb-4">Speed Variations Over Time</h2>

                            {/* Timeline Visualization */}
                            <div className="mb-6">
                                <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
                                    <span>0s</span>
                                    <span>{Math.round(session.duration_seconds)}s</span>
                                </div>

                                {/* Timeline Bar */}
                                <div className="relative h-12 bg-gray-100 rounded-lg overflow-hidden">
                                    {session.speed_events.map((speed, index) => {
                                        const leftPosition = (speed.start_time / session.duration_seconds) * 100;
                                        const duration = speed.end_time - speed.start_time;
                                        const width = (duration / session.duration_seconds) * 100;
                                        const color = speed.speed_type === 'faster' ? 'bg-red-500' : 'bg-blue-500';
                                        const intensity = Math.abs(speed.relative_change - 1) * 0.5 + 0.5; // 0.5 to 1.0 opacity

                                        return (
                                            <div
                                                key={index}
                                                className={`absolute top-0 h-full ${color} hover:opacity-100 transition-opacity`}
                                                style={{
                                                    left: `${leftPosition}%`,
                                                    width: `${Math.max(width, 0.5)}%`,
                                                    opacity: Math.min(intensity, 1)
                                                }}
                                                title={`${speed.speed_type}: ${speed.relative_change.toFixed(2)}x at ${speed.start_time.toFixed(1)}s-${speed.end_time.toFixed(1)}s`}
                                            />
                                        );
                                    })}
                                </div>

                                {/* Legend */}
                                <div className="flex items-center space-x-6 mt-3">
                                    <div className="flex items-center space-x-2">
                                        <div className="w-4 h-4 bg-red-500 rounded"></div>
                                        <span className="text-sm text-gray-600">Faster Speech ({'>'}1.0x)</span>
                                    </div>
                                    <div className="flex items-center space-x-2">
                                        <div className="w-4 h-4 bg-blue-500 rounded"></div>
                                        <span className="text-sm text-gray-600">Slower Speech ({'<'}1.0x)</span>
                                    </div>
                                    <div className="text-xs text-gray-500 ml-4">
                                        *Opacity indicates intensity of speed change
                                    </div>
                                </div>
                            </div>

                            {/* Line Chart */}
                            <div className="h-80">
                                <ResponsiveContainer width="100%" height="100%">
                                    <LineChart data={speedEventsData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="name" />
                                        <YAxis />
                                        <Tooltip formatter={(value: any) => [Number(value).toFixed(2), 'Speed Multiplier']} />
                                        <Line type="monotone" dataKey="Speed Multiplier" stroke="#EF4444" strokeWidth={2} />
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>

                            <div className="mt-4 text-sm text-gray-600">
                                <p><strong>Timeline:</strong> Shows when speed changes occur during your speech. Red = faster, Blue = slower.</p>
                                <p><strong>Chart:</strong> Shows speed multiplier over time. Values above 1.0 = faster, below 1.0 = slower than average.</p>
                            </div>
                        </div>
                    )}

                    {/* Pitch Events Chart */}
                    {pitchEventsData.length > 0 && (
                        <div className="bg-white border border-gray-200 rounded-lg p-6">
                            <h2 className="text-xl font-bold text-gray-900 mb-4">Pitch Stress Events</h2>
                            <div className="h-80">
                                <ResponsiveContainer width="100%" height="100%">
                                    <LineChart data={pitchEventsData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="name" />
                                        <YAxis />
                                        <Tooltip formatter={(value: any) => [Number(value).toFixed(2), 'Pitch Change']} />
                                        <Line type="monotone" dataKey="Pitch Change" stroke="#8B5CF6" strokeWidth={2} />
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    )}

                    {/* Pause Events Timeline */}
                    {pauseTimelineData.length > 0 && (
                        <div className="bg-white border border-gray-200 rounded-lg p-6">
                            <h2 className="text-xl font-bold text-gray-900 mb-4">Pause Events Timeline</h2>

                            {/* Timeline Visualization */}
                            <div className="mb-6">
                                <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
                                    <span>0s</span>
                                    <span>{Math.round(session.duration_seconds)}s</span>
                                </div>

                                {/* Timeline Bar */}
                                <div className="relative h-12 bg-gray-100 rounded-lg overflow-hidden">
                                    {session.pause_events.map((pause, index) => {
                                        const leftPosition = (pause.start_time / session.duration_seconds) * 100;
                                        const width = (pause.duration / session.duration_seconds) * 100;
                                        const color =
                                            pause.pause_type === 'long pause' ? 'bg-red-500' :
                                                pause.pause_type === 'master pause' ? 'bg-yellow-500' : 'bg-green-500';

                                        return (
                                            <div
                                                key={index}
                                                className={`absolute top-0 h-full ${color} opacity-80 hover:opacity-100 transition-opacity`}
                                                style={{
                                                    left: `${leftPosition}%`,
                                                    width: `${Math.max(width, 0.5)}%`
                                                }}
                                                title={`${pause.pause_type}: ${pause.duration.toFixed(1)}s at ${pause.start_time.toFixed(1)}s`}
                                            />
                                        );
                                    })}
                                </div>

                                {/* Legend */}
                                <div className="flex items-center space-x-6 mt-3">
                                    <div className="flex items-center space-x-2">
                                        <div className="w-4 h-4 bg-red-500 rounded"></div>
                                        <span className="text-sm text-gray-600">Long Pause</span>
                                    </div>
                                    <div className="flex items-center space-x-2">
                                        <div className="w-4 h-4 bg-yellow-500 rounded"></div>
                                        <span className="text-sm text-gray-600">Master Pause</span>
                                    </div>
                                    <div className="flex items-center space-x-2">
                                        <div className="w-4 h-4 bg-green-500 rounded"></div>
                                        <span className="text-sm text-gray-600">Brief Pause</span>
                                    </div>
                                </div>
                            </div>

                            {/* Line Chart */}
                            <div className="h-80">
                                <ResponsiveContainer width="100%" height="100%">
                                    <LineChart data={pauseTimelineData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="name" />
                                        <YAxis />
                                        <Tooltip formatter={(value: any) => [Number(value).toFixed(2) + 's', 'Duration']} />
                                        <Line type="monotone" dataKey="Duration" stroke="#06B6D4" strokeWidth={2} />
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>

                            <div className="mt-4 text-sm text-gray-600">
                                <p><strong>Timeline:</strong> Shows when pauses occur during your speech. Hover over colored bars to see details.</p>
                                <p><strong>Chart:</strong> Shows pause duration over time for pattern analysis.</p>
                            </div>
                        </div>
                    )}

                </div>

                {/* FEEDBACK SECTION */}
                <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4 mb-6 mt-6">
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center">
                        <span className="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm mr-3">🎯</span>
                        AI Feedback Analysis
                    </h1>
                    <p className="text-gray-600 text-sm mt-2">Comprehensive feedback comparison for research study effectiveness</p>
                </div>


                {/* Comprehensive Feedback Analysis */}
                    {userSelfRating && (
                        <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
                            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
                                <span className="w-8 h-8 bg-purple-500 text-white rounded-full flex items-center justify-center text-sm mr-3">👤</span>
                                Self-Rating vs AI Analysis Comparison
                            </h2>
                            
                            <div className="mb-4 p-3 bg-purple-50 border border-purple-200 rounded-lg">
                                <p className="text-purple-800 text-sm">
                                    <strong>Research Insight:</strong> This comparison shows how your self-perception aligns with AI analysis, 
                                    helping identify areas of awareness and blind spots in speech evaluation.
                                </p>
                            </div>

                            {/* CSSEF Criteria Comparison */}
                            <div className="space-y-4">
                                {Object.entries(userSelfRating.ratings || {}).map(([criterion, ratingData]: [string, any]) => {
                                    // Get AI score for this criterion from session feedback
                                    const aiScore = session?.full_analysis_results?.feedback?.cssef_evaluation?.[criterion]?.score;
                                    
                                    const criterionTitle = criterion
                                        .replace('C1_topic_choice', 'Topic Choice & Focus')
                                        .replace('C2_purpose', 'Thesis & Purpose')
                                        .replace('C3_supporting_material', 'Supporting Materials')
                                        .replace('C4_organization', 'Organization & Structure')
                                        .replace('C5_language_use', 'Language Use')
                                        .replace('C6_vocal_variety', 'Vocal Variety & Delivery')
                                        .replace('C7_pronunciation_and_grammar', 'Pronunciation & Grammar')
                                        .replace('C8_physical_behaviors', 'Physical Behaviors');
                                    
                                    const userScore = ratingData.score;
                                    const hasUserRating = userScore !== null && userScore !== undefined;
                                    const difference = hasUserRating && aiScore ? Math.abs(userScore - aiScore) : null;
                                    
                                    return (
                                        <div key={criterion} className="border border-gray-200 rounded-lg p-4">
                                            <div className="flex items-center justify-between mb-3">
                                                <h4 className="font-medium text-gray-900">{criterionTitle}</h4>
                                                {difference !== null ? (
                                                    <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                                                        difference <= 1 ? 'bg-green-100 text-green-800' :
                                                        difference <= 2 ? 'bg-yellow-100 text-yellow-800' :
                                                        'bg-red-100 text-red-800'
                                                    }`}>
                                                        {difference <= 1 ? 'Close match' :
                                                         difference <= 2 ? 'Moderate difference' :
                                                         'Large difference'}
                                                    </div>
                                                ) : !hasUserRating ? (
                                                    <div className="px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                                                        Not self-rated
                                                    </div>
                                                ) : null}
                                            </div>
                                            
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3">
                                                {/* User Self-Rating */}
                                                <div className={`p-3 rounded-lg ${hasUserRating ? 'bg-purple-50' : 'bg-gray-50'}`}>
                                                    <div className="flex items-center justify-between mb-2">
                                                        <span className={`text-sm font-medium ${hasUserRating ? 'text-purple-800' : 'text-gray-600'}`}>
                                                            Your Rating
                                                        </span>
                                                        {hasUserRating ? (
                                                            <span className="text-lg font-bold text-purple-900">{userScore}/10</span>
                                                        ) : (
                                                            <span className="text-sm text-gray-500 italic">Not Rated</span>
                                                        )}
                                                    </div>
                                                    <div className={`w-full rounded-full h-2 ${hasUserRating ? 'bg-purple-200' : 'bg-gray-200'}`}>
                                                        {hasUserRating && (
                                                            <div 
                                                                className="bg-purple-600 h-2 rounded-full"
                                                                style={{ width: `${(userScore / 10) * 100}%` }}
                                                            />
                                                        )}
                                                    </div>
                                                </div>
                                                
                                                {/* AI Rating */}
                                                {aiScore ? (
                                                    <div className="bg-blue-50 p-3 rounded-lg">
                                                        <div className="flex items-center justify-between mb-2">
                                                            <span className="text-sm font-medium text-blue-800">AI Analysis</span>
                                                            <span className="text-lg font-bold text-blue-900">{aiScore}/10</span>
                                                        </div>
                                                        <div className="w-full bg-blue-200 rounded-full h-2">
                                                            <div 
                                                                className="bg-blue-600 h-2 rounded-full"
                                                                style={{ width: `${(aiScore / 10) * 100}%` }}
                                                            />
                                                        </div>
                                                    </div>
                                                ) : (
                                                    <div className="bg-gray-50 p-3 rounded-lg">
                                                        <div className="flex items-center justify-between mb-2">
                                                            <span className="text-sm font-medium text-gray-600">AI Analysis</span>
                                                            <span className="text-sm text-gray-500 italic">Not Available</span>
                                                        </div>
                                                        <div className="w-full bg-gray-200 rounded-full h-2">
                                                            {/* Empty progress bar */}
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                            
                                            {/* Analysis */}
                                            {difference !== null ? (
                                                <div className="text-sm text-gray-600 mb-2">
                                                    <strong>Difference:</strong> {difference.toFixed(1)} points
                                                    {userScore > aiScore ? ' (You rated higher)' : userScore < aiScore ? ' (AI rated higher)' : ' (Perfect match!)'}
                                                </div>
                                            ) : hasUserRating && !aiScore ? (
                                                <div className="text-sm text-gray-600 mb-2">
                                                    <strong>Note:</strong> You provided a self-rating but AI analysis is not available for this criterion.
                                                </div>
                                            ) : !hasUserRating && aiScore ? (
                                                <div className="text-sm text-gray-600 mb-2">
                                                    <strong>Note:</strong> AI provided analysis but you didn't rate this criterion.
                                                </div>
                                            ) : (
                                                <div className="text-sm text-gray-600 mb-2">
                                                    <strong>Note:</strong> Neither self-rating nor AI analysis available for this criterion.
                                                </div>
                                            )}
                                            
                                            {/* User Comment */}
                                            {ratingData.comment && (
                                                <div className="bg-gray-50 p-3 rounded-lg mt-2">
                                                    <div className="text-sm font-medium text-gray-700 mb-1">Your Reflection:</div>
                                                    <div className="text-sm text-gray-600 italic">"{ratingData.comment}"</div>
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                            
                            {/* Overall Self-Rating Summary */}
                            {userSelfRating.overall_comment && (
                                <div className="mt-6 p-4 bg-gray-50 border border-gray-200 rounded-lg">
                                    <h4 className="font-medium text-gray-900 mb-2">Your Overall Reflection</h4>
                                    <p className="text-gray-700 text-sm italic">"{userSelfRating.overall_comment}"</p>
                                    
                                    {userSelfRating.confidence_level && (
                                        <div className="mt-3 flex items-center">
                                            <span className="text-sm text-gray-600 mr-2">Confidence in self-assessment:</span>
                                            <div className="flex items-center space-x-1">
                                                {[1, 2, 3, 4, 5].map((level) => (
                                                    <div
                                                        key={level}
                                                        className={`w-3 h-3 rounded-full ${
                                                            level <= userSelfRating.confidence_level
                                                                ? 'bg-yellow-400'
                                                                : 'bg-gray-300'
                                                        }`}
                                                    />
                                                ))}
                                                <span className="text-sm text-gray-600 ml-2">
                                                    ({userSelfRating.confidence_level}/5)
                                                </span>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    )}

                    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6">
                        <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                            <span className="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm mr-3">AI</span>
                            Comprehensive Feedback Analysis
                        </h2>
                        
                        {/* Research Context Banner */}
                        <div className="bg-white border-l-4 border-blue-500 p-4 mb-6 rounded-r-lg">
                            <div className="flex items-center">
                                <div className="text-blue-500 font-semibold text-sm">RESEARCH STUDY</div>
                            </div>
                            <p className="text-gray-700 text-sm mt-1">
                                This analysis compares <strong>context-aware feedback</strong> vs <strong>general feedback</strong> to measure effectiveness in speech improvement.
                            </p>
                        </div>

                        {/* Two-Column Feedback Comparison */}
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                            
                            {/* Context-Aware Feedback */}
                            <div className="bg-white border border-green-200 rounded-lg p-5">
                                <div className="flex items-center mb-4">
                                    <div className="w-6 h-6 bg-green-500 text-white rounded-full flex items-center justify-center text-xs mr-2">✓</div>
                                    <h3 className="text-lg font-bold text-green-800">Context-Aware Feedback</h3>
                                </div>
                                
                                {/* Summary */}
                                {session.full_analysis_results?.feedback?.summary && (
                                    <div className="mb-4">
                                        <h4 className="font-semibold text-gray-900 mb-2">Summary</h4>
                                        <p className="text-gray-700 text-sm bg-green-50 p-3 rounded-lg">{session.full_analysis_results.feedback.summary}</p>
                                    </div>
                                )}

                                {/* Suggestions */}
                                {session.full_analysis_results?.feedback?.suggestions && (
                                    <div className="mb-4">
                                        <h4 className="font-semibold text-gray-900 mb-2">Key Suggestions</h4>
                                        <ul className="space-y-2">
                                            {session.full_analysis_results.feedback.suggestions.map((suggestion, index) => (
                                                <li key={index} className="flex items-start space-x-2 text-sm">
                                                    <div className="w-1.5 h-1.5 bg-green-500 rounded-full mt-2 flex-shrink-0"></div>
                                                    <span className="text-gray-700">{suggestion}</span>
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}

                                {/* Motivation */}
                                {session.full_analysis_results?.feedback?.motivation && (
                                    <div className="mb-4">
                                        <h4 className="font-semibold text-blue-800 mb-2 flex items-center">
                                            <span className="w-4 h-4 bg-blue-500 text-white rounded-full flex items-center justify-center text-xs mr-2">💪</span>
                                            Motivation
                                        </h4>
                                        <p className="text-gray-700 text-sm bg-blue-50 p-3 rounded-lg border-l-4 border-blue-500">{session.full_analysis_results.feedback.motivation}</p>
                                    </div>
                                )}

                                {/* Improved Excerpt */}
                                {session.full_analysis_results?.feedback?.improved_excerpt && (
                                    <div className="mb-4">
                                        <h4 className="font-semibold text-gray-900 mb-2">Improved Version</h4>
                                        <div className="bg-green-50 border-l-4 border-green-500 p-3 rounded-r-lg">
                                            <p className="text-gray-700 italic text-sm">"{session.full_analysis_results.feedback.improved_excerpt}"</p>
                                        </div>
                                    </div>
                                )}

                                {/* Strengths */}
                                {session.full_analysis_results?.feedback?.strengths && session.full_analysis_results.feedback.strengths.length > 0 && (
                                    <div className="mb-4">
                                        <h4 className="font-semibold text-green-800 mb-2 flex items-center">
                                            <span className="w-4 h-4 bg-green-500 text-white rounded-full flex items-center justify-center text-xs mr-2">+</span>
                                            Strengths
                                        </h4>
                                        <ul className="space-y-2">
                                            {session.full_analysis_results.feedback.strengths.map((strength, index) => (
                                                <li key={index} className="text-sm bg-green-50 p-2 rounded border-l-2 border-green-300">
                                                    <div className="font-medium text-green-700">{strength.title}</div>
                                                    {strength.details && <div className="text-gray-600 text-xs mt-1">{strength.details}</div>}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}

                                {/* Issues */}
                                {session.full_analysis_results?.feedback?.issues && session.full_analysis_results.feedback.issues.length > 0 && (
                                    <div className="mb-4">
                                        <h4 className="font-semibold text-red-800 mb-2 flex items-center">
                                            <span className="w-4 h-4 bg-red-500 text-white rounded-full flex items-center justify-center text-xs mr-2">!</span>
                                            Issues to Address
                                        </h4>
                                        <ul className="space-y-2">
                                            {session.full_analysis_results.feedback.issues.map((issue, index) => (
                                                <li key={index} className="text-sm bg-red-50 p-2 rounded border-l-2 border-red-300">
                                                    <div className="font-medium text-red-700">{issue.title}</div>
                                                    {issue.details && <div className="text-gray-600 text-xs mt-1">{issue.details}</div>}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}

                                {/* Micro Exercises */}
                                {session.full_analysis_results?.feedback?.micro_exercises && (
                                    <div className="mb-4">
                                        <h4 className="font-semibold text-purple-800 mb-2 flex items-center">
                                            <span className="w-4 h-4 bg-purple-500 text-white rounded-full flex items-center justify-center text-xs mr-2">Ex</span>
                                            Recommended Exercises
                                        </h4>
                                        <div className="space-y-3">
                                            {session.full_analysis_results.feedback.micro_exercises.map((exercise, index) => (
                                                <div key={index} className="p-3 border border-purple-200 rounded-lg bg-purple-50">
                                                    <div className="flex items-start justify-between mb-2">
                                                        <h5 className="font-bold text-purple-900 text-sm">{exercise.title}</h5>
                                                        <span className="text-xs bg-purple-200 text-purple-800 px-2 py-1 rounded-full">{exercise.duration}</span>
                                                    </div>
                                                    <div className="text-xs text-purple-700 mb-2 font-medium">Focus: {exercise.focus_area}</div>
                                                    <p className="text-gray-700 text-xs">{exercise.description}</p>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* CSSEF Evaluation for Context-Aware Feedback */}
                                {session.full_analysis_results?.feedback?.cssef_evaluation && (
                                    <div className="mb-4">
                                        <h4 className="font-semibold text-gray-900 mb-2">CSSEF Evaluation</h4>
                                        <div className="grid gap-2">
                                            {Object.entries(session.full_analysis_results.feedback.cssef_evaluation).map(([key, value]: [string, any]) => (
                                                <div key={key} className="p-2 bg-gray-50 rounded">
                                                    <div className="flex justify-between items-center">
                                                        <span className="text-sm font-medium">{key.replace('C', '').replace('_', ' ').replace(/\d+/, '').trim()}</span>
                                                        <span className="text-sm font-bold text-green-600">{value.score || 0}/10</span>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                   {/* Context-Specific Tips */}
                                {session.full_analysis_results?.feedback?.context_specific_tips && (
                                    <div className="mb-4">
                                        <h4 className="font-semibold text-green-800 mb-2 flex items-center">
                                            <span className="w-4 h-4 bg-green-500 text-white rounded-full flex items-center justify-center text-xs mr-2">🎯</span>
                                            Context-Specific Tips
                                        </h4>
                                        <ul className="space-y-2">
                                            {session.full_analysis_results.feedback.context_specific_tips.map((tip, index) => (
                                                <li key={index} className="flex items-start space-x-2 text-sm bg-green-50 p-2 rounded border-l-2 border-green-300">
                                                    <div className="w-1.5 h-1.5 bg-green-500 rounded-full mt-2 flex-shrink-0"></div>
                                                    <span className="text-gray-700">{tip}</span>
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                            </div>

                            {/* General Feedback */}
                            <div className="bg-white border border-orange-200 rounded-lg p-5">
                                <div className="flex items-center mb-4">
                                    <div className="w-6 h-6 bg-orange-500 text-white rounded-full flex items-center justify-center text-xs mr-2">⚠</div>
                                    <h3 className="text-lg font-bold text-orange-800">General Feedback</h3>
                                </div>
                                
                                {/* Check if feedback_without_context is structured or string */}
                                {session.full_analysis_results?.feedback_without_context && (
                                    <>
                                        {typeof session.full_analysis_results.feedback_without_context === 'string' ? (
                                            /* Legacy string feedback */
                                            <div className="text-sm text-gray-700 bg-orange-50 p-3 rounded-lg whitespace-pre-line">
                                                <ReactMarkdown>{session.full_analysis_results.feedback_without_context}</ReactMarkdown>
                                            </div>
                                        ) : (
                                            /* New structured feedback */
                                            <>
                                                {/* Summary */}
                                                {session.full_analysis_results.feedback_without_context.summary && (
                                                    <div className="mb-4">
                                                        <h4 className="font-semibold text-gray-900 mb-2">Summary</h4>
                                                        <p className="text-gray-700 text-sm bg-orange-50 p-3 rounded-lg">{session.full_analysis_results.feedback_without_context.summary}</p>
                                                    </div>
                                                )}

                                                {/* Suggestions */}
                                                {session.full_analysis_results.feedback_without_context.suggestions && (
                                                    <div className="mb-4">
                                                        <h4 className="font-semibold text-gray-900 mb-2">Key Suggestions</h4>
                                                        <ul className="space-y-2">
                                                            {session.full_analysis_results.feedback_without_context.suggestions.map((suggestion, index) => (
                                                                <li key={index} className="flex items-start space-x-2 text-sm">
                                                                    <div className="w-1.5 h-1.5 bg-orange-500 rounded-full mt-2 flex-shrink-0"></div>
                                                                    <span className="text-gray-700">{suggestion}</span>
                                                                </li>
                                                            ))}
                                                        </ul>
                                                    </div>
                                                )}

                                                {/* Motivation */}
                                                {session.full_analysis_results.feedback_without_context.motivation && (
                                                    <div className="mb-4">
                                                        <h4 className="font-semibold text-blue-800 mb-2 flex items-center">
                                                            <span className="w-4 h-4 bg-blue-500 text-white rounded-full flex items-center justify-center text-xs mr-2">💪</span>
                                                            Motivation
                                                        </h4>
                                                        <p className="text-gray-700 text-sm bg-blue-50 p-3 rounded-lg border-l-4 border-blue-500">{session.full_analysis_results.feedback_without_context.motivation}</p>
                                                    </div>
                                                )}

                                                {/* Improved Excerpt */}
                                                {session.full_analysis_results.feedback_without_context.improved_excerpt && (
                                                    <div className="mb-4">
                                                        <h4 className="font-semibold text-gray-900 mb-2">Improved Version</h4>
                                                        <div className="bg-orange-50 border-l-4 border-orange-500 p-3 rounded-r-lg">
                                                            <p className="text-gray-700 italic text-sm">"{session.full_analysis_results.feedback_without_context.improved_excerpt}"</p>
                                                        </div>
                                                    </div>
                                                )}

                                                {/* Strengths */}
                                                {session.full_analysis_results.feedback_without_context.strengths && session.full_analysis_results.feedback_without_context.strengths.length > 0 && (
                                                    <div className="mb-4">
                                                        <h4 className="font-semibold text-green-800 mb-2 flex items-center">
                                                            <span className="w-4 h-4 bg-green-500 text-white rounded-full flex items-center justify-center text-xs mr-2">+</span>
                                                            Strengths
                                                        </h4>
                                                        <ul className="space-y-2">
                                                            {session.full_analysis_results.feedback_without_context.strengths.map((strength, index) => (
                                                                <li key={index} className="text-sm bg-green-50 p-2 rounded border-l-2 border-green-300">
                                                                    <div className="font-medium text-green-700">{strength.title}</div>
                                                                    {strength.details && <div className="text-gray-600 text-xs mt-1">{strength.details}</div>}
                                                                </li>
                                                            ))}
                                                        </ul>
                                                    </div>
                                                )}

                                                {/* Issues */}
                                                {session.full_analysis_results.feedback_without_context.issues && session.full_analysis_results.feedback_without_context.issues.length > 0 && (
                                                    <div className="mb-4">
                                                        <h4 className="font-semibold text-red-800 mb-2 flex items-center">
                                                            <span className="w-4 h-4 bg-red-500 text-white rounded-full flex items-center justify-center text-xs mr-2">!</span>
                                                            Issues to Address
                                                        </h4>
                                                        <ul className="space-y-2">
                                                            {session.full_analysis_results.feedback_without_context.issues.map((issue, index) => (
                                                                <li key={index} className="text-sm bg-red-50 p-2 rounded border-l-2 border-red-300">
                                                                    <div className="font-medium text-red-700">{issue.title}</div>
                                                                    {issue.details && <div className="text-gray-600 text-xs mt-1">{issue.details}</div>}
                                                                </li>
                                                            ))}
                                                        </ul>
                                                    </div>
                                                )}

                                                {/* Micro Exercises */}
                                                {session.full_analysis_results.feedback_without_context.micro_exercises && (
                                                    <div className="mb-4">
                                                        <h4 className="font-semibold text-purple-800 mb-2 flex items-center">
                                                            <span className="w-4 h-4 bg-purple-500 text-white rounded-full flex items-center justify-center text-xs mr-2">Ex</span>
                                                            Recommended Exercises
                                                        </h4>
                                                        <div className="space-y-3">
                                                            {session.full_analysis_results.feedback_without_context.micro_exercises.map((exercise, index) => (
                                                                <div key={index} className="p-3 border border-purple-200 rounded-lg bg-purple-50">
                                                                    <div className="flex items-start justify-between mb-2">
                                                                        <h5 className="font-bold text-purple-900 text-sm">{exercise.title}</h5>
                                                                        <span className="text-xs bg-purple-200 text-purple-800 px-2 py-1 rounded-full">{exercise.duration}</span>
                                                                    </div>
                                                                    <div className="text-xs text-purple-700 mb-2 font-medium">Focus: {exercise.focus_area}</div>
                                                                    <p className="text-gray-700 text-xs">{exercise.description}</p>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}

                                                {/* CSSEF Evaluation for General Feedback */}
                                                {session.full_analysis_results.feedback_without_context.cssef_evaluation && (
                                                    <div className="mb-4">
                                                        <h4 className="font-semibold text-gray-900 mb-2">CSSEF Evaluation</h4>
                                                        <div className="grid gap-2">
                                                            {Object.entries(session.full_analysis_results.feedback_without_context.cssef_evaluation).map(([key, value]: [string, any]) => (
                                                                <div key={key} className="p-2 bg-gray-50 rounded">
                                                                    <div className="flex justify-between items-center">
                                                                        <span className="text-sm font-medium">{key.replace('C', '').replace('_', ' ').replace(/\d+/, '').trim()}</span>
                                                                        <span className="text-sm font-bold text-orange-600">{value.score || 0}/10</span>
                                                                    </div>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}
                                            </>
                                        )}
                                    </>
                                )}
                            </div>
                        </div>

                    </div>

                {/* Audio/Video Player */}
                {session.media_url && (
                    <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
                        <h2 className="text-xl font-bold text-gray-900 mb-4">Recording</h2>
                        <MediaPlayer
                            mediaUrl={session.media_url}
                            mediaType={session.media_type as 'audio' | 'video'}
                            originalFilename={session.original_filename}
                            sessionId={session.id}
                            onUrlRefresh={handleMediaUrlRefresh}
                        />
                    </div>
                )}



                {/* Add Self-Rating Option */}
                {!userSelfRating && (
                    <div className="bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 rounded-lg p-6 mb-6">
                        <div className="flex items-center justify-between">
                            <div>
                                <h2 className="text-xl font-bold text-gray-900 mb-2 flex items-center">
                                    <span className="w-8 h-8 bg-purple-500 text-white rounded-full flex items-center justify-center text-sm mr-3">⭐</span>
                                    Rate Your Performance
                                </h2>
                                <p className="text-gray-600 text-sm">
                                    Help our research by providing your self-assessment. Compare your perception with AI analysis!
                                </p>
                            </div>
                            <button
                                onClick={() => {
                                    // For now, navigate to a separate rating page or show inline form
                                    toast.success("Self-rating feature coming soon! This will allow you to rate your speech and compare with AI analysis.");
                                }}
                                className="bg-purple-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-purple-700 transition-colors"
                            >
                                Add Self-Rating
                            </button>
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
