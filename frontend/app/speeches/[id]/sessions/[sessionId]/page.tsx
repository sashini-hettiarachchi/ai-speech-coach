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
    // New response structure
    cssef_scores?: {
        c1_topic_choice?: {
            comment: string;
            improvement: string;
            score: number;
        };
        c2_purpose?: {
            comment: string;
            improvement: string;
            score: number;
        };
        c3_supporting?: {
            comment: string;
            improvement: string;
            score: number;
        };
        c4_organization?: {
            comment: string;
            improvement: string;
            score: number;
        };
        c5_language?: {
            comment: string;
            improvement: string;
            score: number;
        };
        c6_vocal_variety?: {
            comment: string;
            improvement: string;
            score: number;
        };
        c7_pronunciation?: {
            comment: string;
            improvement: string;
            score: number;
        };
    };
    feedback_summary?: {
        summary: string;
        improvements: string[];
        strengths: string[];
    };
    overall_score?: number;
    // Legacy CSSEF structure (for backward compatibility)
    c1_topic_choice?: {
        comment: string;
        improvement: string;
        score: number;
    };
    c2_purpose?: {
        comment: string;
        improvement: string;
        score: number;
    };
    c3_supporting?: {
        comment: string;
        improvement: string;
        score: number;
    };
    c4_organization?: {
        comment: string;
        improvement: string;
        score: number;
    };
    c5_language?: {
        comment: string;
        improvement: string;
        score: number;
    };
    c6_vocal_variety?: {
        comment: string;
        improvement: string;
        score: number;
    };
    c7_pronunciation?: {
        comment: string;
        improvement: string;
        score: number;
    };
    // New fields
    revised_speech_text?: string;
    revised_speech_audio_url?: string;
    improvements?: string[];
    strengths?: string[];
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

        } catch (error) {
            console.error("Error loading session data:", error);
            toast.error("Failed to load session data");
        } finally {
            setLoading(false);
        }
    }; const handleDeleteSession = async () => {
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

    // Get score label based on 1-5 range
    const getScoreLabel = (score: number) => {
        if (score <= 2) return { label: 'Unsatisfactory', color: 'text-red-600' };
        if (score > 2 && score < 4) return { label: 'Satisfactory', color: 'text-yellow-600' };
        if (score >= 4) return { label: 'Excellent', color: 'text-green-600' };
        return { label: 'Not Rated', color: 'text-gray-500' };
    };

    // Get CSSEF scores for display
    const getCSSEFScores = () => {
        // Check for the new cssef_scores structure first
        if (session?.cssef_scores) {
            const criteria = [
                { key: 'c1_topic_choice', title: 'Topic Choice & Focus', data: session.cssef_scores.c1_topic_choice },
                { key: 'c2_purpose', title: 'Thesis & Purpose', data: session.cssef_scores.c2_purpose },
                { key: 'c3_supporting', title: 'Supporting Materials', data: session.cssef_scores.c3_supporting },
                { key: 'c4_organization', title: 'Organization & Structure', data: session.cssef_scores.c4_organization },
                { key: 'c5_language', title: 'Language Use', data: session.cssef_scores.c5_language },
                { key: 'c6_vocal_variety', title: 'Vocal Variety & Delivery', data: session.cssef_scores.c6_vocal_variety },
                { key: 'c7_pronunciation', title: 'Pronunciation & Grammar', data: session.cssef_scores.c7_pronunciation }
            ];

            return criteria.filter(criterion => criterion.data).map(criterion => ({
                criterion: criterion.title,
                score: criterion.data?.score || 0,
                comment: criterion.data?.comment || '',
                improvement: criterion.data?.improvement || ''
            }));
        }

        // Check for legacy direct properties structure
        if (session?.c1_topic_choice || session?.c2_purpose || session?.c3_supporting ||
            session?.c4_organization || session?.c5_language || session?.c6_vocal_variety ||
            session?.c7_pronunciation) {

            const criteria = [
                { key: 'c1_topic_choice', title: 'Topic Choice & Focus', data: session.c1_topic_choice },
                { key: 'c2_purpose', title: 'Thesis & Purpose', data: session.c2_purpose },
                { key: 'c3_supporting', title: 'Supporting Materials', data: session.c3_supporting },
                { key: 'c4_organization', title: 'Organization & Structure', data: session.c4_organization },
                { key: 'c5_language', title: 'Language Use', data: session.c5_language },
                { key: 'c6_vocal_variety', title: 'Vocal Variety & Delivery', data: session.c6_vocal_variety },
                { key: 'c7_pronunciation', title: 'Pronunciation & Grammar', data: session.c7_pronunciation }
            ];

            return criteria.filter(criterion => criterion.data).map(criterion => ({
                criterion: criterion.title,
                score: criterion.data?.score || 0,
                comment: criterion.data?.comment || '',
                improvement: criterion.data?.improvement || ''
            }));
        }

        // Fallback to old structure
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

                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mt-4">
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
                        {session.overall_score && (
                            <div className="text-center">
                                <div className="text-2xl font-bold text-purple-600">{session.overall_score?.toFixed(1)}/5</div>
                                <div className="text-sm text-gray-600">Overall Score</div>
                                <div className={`text-xs font-medium ${getScoreLabel(session.overall_score).color}`}>
                                    {getScoreLabel(session.overall_score).label}
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Transcript */}
                {session.transcript && (
                    <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
                        <h2 className="text-xl font-bold text-gray-900 mb-4">Transcript</h2>
                        <div className="bg-gray-50 rounded-lg p-4">
                            <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                                {session.transcript}
                            </p>
                        </div>
                    </div>
                )}

                {/* Audio/Video Player */}
                {session.media_url && (
                    <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
                        <h2 className="text-xl font-bold text-gray-900 mb-4">Original Recording</h2>
                        <MediaPlayer
                            mediaUrl={session.media_url}
                            mediaType={session.media_type as 'audio' | 'video'}
                            originalFilename={session.original_filename}
                            sessionId={session.id}
                            onUrlRefresh={handleMediaUrlRefresh}
                        />
                    </div>
                )}

                {/* FEEDBACK SECTION */}
                <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4 mb-6 mt-6">
                    <h1 className="text-2xl font-bold text-gray-900 flex items-center">
                        <span className="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm mr-3">🎯</span>
                        AI Feedback Analysis
                    </h1>
                    <p className="text-gray-600 text-sm mt-2">Comprehensive feedback comparison for research study effectiveness</p>
                </div>


                {/* Comprehensive Feedback Analysis */}

                <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6">
                    <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                        <span className="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm mr-3">AI</span>
                        Comprehensive Feedback Analysis
                    </h2>

                    {/* Feedback Summary */}
                    {session.feedback_summary && (
                        <div className="mb-6 bg-white border border-gray-200 rounded-lg p-6">
                            <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
                                <span className="w-6 h-6 bg-green-500 text-white rounded-full flex items-center justify-center text-xs mr-2">📝</span>
                                Executive Summary
                            </h3>
                            
                            {session.feedback_summary.summary && (
                                <div className="mb-4">
                                    <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded-r-lg">
                                        <p className="text-gray-700 leading-relaxed">
                                            {session.feedback_summary.summary}
                                        </p>
                                    </div>
                                </div>
                            )}

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {/* Strengths */}
                                {session.feedback_summary.strengths && session.feedback_summary.strengths.length > 0 && (
                                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                                        <h4 className="font-semibold text-green-800 mb-2 flex items-center">
                                            <span className="w-4 h-4 bg-green-500 text-white rounded-full flex items-center justify-center text-xs mr-2">✓</span>
                                            Key Strengths
                                        </h4>
                                        <ul className="space-y-1">
                                            {session.feedback_summary.strengths.map((strength, index) => (
                                                <li key={index} className="text-green-700 text-sm flex items-start">
                                                    <span className="text-green-500 mr-2">•</span>
                                                    {strength}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}

                                {/* Improvements */}
                                {session.feedback_summary.improvements && session.feedback_summary.improvements.length > 0 && (
                                    <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                                        <h4 className="font-semibold text-orange-800 mb-2 flex items-center">
                                            <span className="w-4 h-4 bg-orange-500 text-white rounded-full flex items-center justify-center text-xs mr-2">📈</span>
                                            Areas for Improvement
                                        </h4>
                                        <ul className="space-y-1">
                                            {session.feedback_summary.improvements.map((improvement, index) => (
                                                <li key={index} className="text-orange-700 text-sm flex items-start">
                                                    <span className="text-orange-500 mr-2">•</span>
                                                    {improvement}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Feedback */}
                    <div className="grid grid-cols-1  gap-6 mb-6">

                        <div className="col-span-1">
                            {/* CSSEF Evaluation */}
                            {cssefScores && cssefScores.length > 0 && (
                                <div className="mb-4">
                                    <h4 className="font-semibold text-gray-900 mb-2">CSSEF Evaluation</h4>

                                    {/* Score Range Legend */}
                                    <div className="mb-4 p-3 bg-gray-50 rounded-lg border border-gray-200">
                                        <div className="text-sm font-medium text-gray-700 mb-2">Score Scale (1-5):</div>
                                        <div className="flex flex-wrap gap-4 text-xs">
                                            <div className="flex items-center">
                                                <div className="w-3 h-3 bg-red-500 rounded-full mr-1"></div>
                                                <span className="text-red-600 font-medium">&lt;2: Unsatisfactory</span>
                                            </div>
                                            <div className="flex items-center">
                                                <div className="w-3 h-3 bg-yellow-500 rounded-full mr-1"></div>
                                                <span className="text-yellow-600 font-medium">2-4: Satisfactory</span>
                                            </div>
                                            <div className="flex items-center">
                                                <div className="w-3 h-3 bg-green-500 rounded-full mr-1"></div>
                                                <span className="text-green-600 font-medium">&gt;=4: Excellent</span>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="grid gap-3">
                                        {cssefScores.map((criterion, index) => {
                                            const scoreLabel = getScoreLabel(criterion.score);
                                            return (
                                                <div key={index} className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                                                    <div className="flex justify-between items-start mb-3">
                                                        <span className="text-sm font-bold text-gray-900">{criterion.criterion}</span>
                                                        <div className="text-right">
                                                            <span className="text-lg font-bold text-blue-600">{criterion.score}/5</span>
                                                            <div className={`text-xs font-medium ${scoreLabel.color}`}>
                                                                {scoreLabel.label}
                                                            </div>
                                                        </div>
                                                    </div>

                                                    {/* Progress bar */}
                                                    <div className="w-full bg-gray-200 rounded-full h-2 mb-3">
                                                        <div
                                                            className="bg-blue-600 h-2 rounded-full"
                                                            style={{ width: `${(criterion.score / 5) * 100}%` }}
                                                        />
                                                    </div>

                                                    {/* Comment and Improvement */}
                                                    <div className="space-y-2">
                                                        {(criterion as any).comment && (
                                                            <div className="text-xs">
                                                                <span className="font-medium text-green-700">Comment: </span>
                                                                <span className="text-gray-700">{(criterion as any).comment}</span>
                                                            </div>
                                                        )}
                                                        {(criterion as any).improvement && (
                                                            <div className="text-xs">
                                                                <span className="font-medium text-orange-700">Improvement: </span>
                                                                <span className="text-gray-700">{(criterion as any).improvement}</span>
                                                            </div>
                                                        )}

                                                        {/* Legacy structure support */}
                                                        {(criterion as any).strengths && (criterion as any).strengths.length > 0 && (
                                                            <div className="text-xs">
                                                                <span className="font-medium text-green-700">Strengths: </span>
                                                                <span className="text-gray-700">{(criterion as any).strengths.join(', ')}</span>
                                                            </div>
                                                        )}
                                                        {(criterion as any).improvements && (criterion as any).improvements.length > 0 && (
                                                            <div className="text-xs">
                                                                <span className="font-medium text-orange-700">Areas for improvement: </span>
                                                                <span className="text-gray-700">{(criterion as any).improvements.join(', ')}</span>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            )}

                            {/* Revised Speech Text */}
                            {session.revised_speech_text && (
                                <div className="mb-4">
                                    <h4 className="font-semibold text-indigo-800 mb-2 flex items-center">
                                        <span className="w-4 h-4 bg-indigo-500 text-white rounded-full flex items-center justify-center text-xs mr-2">✨</span>
                                        Revised Speech Text
                                    </h4>
                                    <div className="bg-indigo-50 border-l-4 border-indigo-500 p-4 rounded-r-lg">
                                        <p className="text-gray-700 text-sm leading-relaxed whitespace-pre-wrap">
                                            {session.revised_speech_text}
                                        </p>
                                    </div>
                                </div>
                            )}

                            {/* Revised Speech Audio Player */}
                            {session.revised_speech_audio_url && (
                                <div className="bg-white border border-green-200 rounded-lg p-6 mb-6">
                                    <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
                                        <span className="w-6 h-6 bg-green-500 text-white rounded-full flex items-center justify-center text-xs mr-2">✨</span>
                                        AI-Generated Improved Speech Audio
                                    </h2>
                                    <p className="text-gray-600 text-sm mb-4">
                                        This is an AI-generated audio version of your improved speech text using text-to-speech technology.
                                    </p>
                                    <MediaPlayer
                                        mediaUrl={session.revised_speech_audio_url}
                                        mediaType="audio"
                                        originalFilename={`revised_speech_${session.id}.mp3`}
                                        sessionId={session.id}
                                        onUrlRefresh={() => { }} // No refresh needed for generated audio
                                    />
                                </div>
                            )}
                        </div>
                    </div>

                </div>


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

                <Toaster
                    position="top-center"
                    reverseOrder={false}
                    toastOptions={{ duration: 3000 }}
                />
            </main>
        </div>
    );
}
