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

// Simple chart components without recharts
const SimpleBarChart = ({ data, title }: { data: any[], title: string }) => (
    <div className="space-y-2">
        <h3 className="font-medium text-gray-700">{title}</h3>
        {data.map((item, index) => (
            <div key={index} className="flex items-center space-x-3">
                <div className="w-20 text-sm text-gray-600 truncate">{item.criterion}</div>
                <div className="flex-1 bg-gray-200 rounded-full h-4">
                    <div
                        className="bg-blue-500 h-4 rounded-full"
                        style={{ width: `${(item.score / 10) * 100}%` }}
                    ></div>
                </div>
                <div className="w-8 text-sm font-medium">{item.score}</div>
            </div>
        ))}
    </div>
);

const SimpleLineChart = ({ data, title }: { data: any[], title: string }) => (
    <div className="space-y-2">
        <h3 className="font-medium text-gray-700">{title}</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {data.map((item, index) => (
                <div key={index} className="p-3 bg-gray-50 rounded-lg">
                    <div className="text-sm text-gray-600">{item.name}</div>
                    <div className={`text-lg font-bold ${item['Speed Multiplier'] > 1 ? 'text-red-500' : 'text-blue-500'
                        }`}>
                        {item['Speed Multiplier']?.toFixed(2)}x
                    </div>
                    <div className="text-xs text-gray-500">{item.type}</div>
                </div>
            ))}
        </div>
    </div>
);

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
        };
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
            console.log("session data", sessionData)
            console.log("speech data", speechData)
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

                {/* Filler Words Analysis */}
                {session.filler_word_details && (
                    <div className="bg-white border border-gray-200 rounded-lg p-6">
                        <h2 className="text-xl font-bold text-gray-900 mb-4">Filler Words Analysis</h2>
                        <FillerWordsChart fillerWords={{
                            fillers: session.filler_word_details.fillers,
                            total: session.filler_word_details.total_fillers
                        }} />
                        <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
                            {Object.entries(session.filler_word_details.fillers).map(([word, count]) => (
                                <div key={word} className="text-center p-3 bg-gray-50 rounded-lg">
                                    <div className="text-2xl font-bold text-orange-600">{count}</div>
                                    <div className="text-sm text-gray-600">"{word}"</div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
                {/* Analysis Results */}
                <div className="space-y-6">
                    {/* CSSEF Evaluation Scores */}
                    {cssefScores && (
                        <div className="bg-white border border-gray-200 rounded-lg p-6">
                            <h2 className="text-xl font-bold text-gray-900 mb-4">CSSEF Evaluation Scores</h2>
                            <div className="h-80">
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={cssefScores} margin={{ top: 20, right: 30, left: 20, bottom: 80 }}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis
                                            dataKey="criterion"
                                            angle={-45}
                                            textAnchor="end"
                                            height={80}
                                            interval={0}
                                        />
                                        <YAxis domain={[0, 10]} />
                                        <Tooltip />
                                        <Bar dataKey="score" fill="#3B82F6" />
                                    </BarChart>
                                </ResponsiveContainer>
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

                            {/* Detailed List */}
                            <div className="mt-6">
                                <h3 className="text-lg font-medium text-gray-900 mb-3">Speed Event Details</h3>
                                <div className="space-y-2">
                                    {session.speed_events.map((speed, index) => (
                                        <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                            <div className="flex items-center space-x-3">
                                                <div className={`w-3 h-3 rounded-full ${speed.speed_type === 'faster' ? 'bg-red-500' : 'bg-blue-500'
                                                    }`}></div>
                                                <div>
                                                    <div className="font-medium capitalize">{speed.speed_type} Speech</div>
                                                    <div className="text-sm text-gray-600">
                                                        {speed.start_time.toFixed(1)}s - {speed.end_time.toFixed(1)}s
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="text-right">
                                                <div className={`font-bold ${speed.speed_type === 'faster' ? 'text-red-600' : 'text-blue-600'
                                                    }`}>
                                                    {speed.relative_change.toFixed(2)}x
                                                </div>
                                                <div className="text-xs text-gray-500">multiplier</div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
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

                            {/* Detailed List */}
                            <div className="mt-6">
                                <h3 className="text-lg font-medium text-gray-900 mb-3">Pause Details</h3>
                                <div className="space-y-2">
                                    {session.pause_events.map((pause, index) => (
                                        <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                            <div className="flex items-center space-x-3">
                                                <div className={`w-3 h-3 rounded-full ${pause.pause_type === 'long pause' ? 'bg-red-500' :
                                                        pause.pause_type === 'master pause' ? 'bg-yellow-500' : 'bg-green-500'
                                                    }`}></div>
                                                <div>
                                                    <div className="font-medium capitalize">{pause.pause_type}</div>
                                                    <div className="text-sm text-gray-600">
                                                        {pause.start_time.toFixed(1)}s - {pause.end_time.toFixed(1)}s
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="text-right">
                                                <div className="font-bold text-gray-900">{pause.duration.toFixed(1)}s</div>
                                                <div className="text-xs text-gray-500">duration</div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div className="mt-4 text-sm text-gray-600">
                                <p><strong>Timeline:</strong> Shows when pauses occur during your speech. Hover over colored bars to see details.</p>
                                <p><strong>Chart:</strong> Shows pause duration over time for pattern analysis.</p>
                            </div>
                        </div>
                    )}



                    {/* Micro Exercises */}
                    {session.full_analysis_results?.feedback?.micro_exercises && (
                        <div className="bg-white border border-gray-200 rounded-lg p-6">
                            <h2 className="text-xl font-bold text-gray-900 mb-4">Recommended Exercises</h2>
                            <div className="space-y-4">
                                {session.full_analysis_results.feedback.micro_exercises.map((exercise, index) => (
                                    <div key={index} className="p-4 border border-gray-200 rounded-lg">
                                        <h3 className="font-bold text-lg text-gray-900">{exercise.title}</h3>
                                        <p className="text-sm text-gray-600 mb-2">Duration: {exercise.duration} • Focus: {exercise.focus_area}</p>
                                        <p className="text-gray-700">{exercise.description}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Key Suggestions */}
                    {session.full_analysis_results?.feedback?.suggestions && (
                        <div className="bg-white border border-gray-200 rounded-lg p-6">
                            <h2 className="text-xl font-bold text-gray-900 mb-4">Key Suggestions</h2>
                            <ul className="space-y-2">
                                {session.full_analysis_results.feedback.suggestions.map((suggestion, index) => (
                                    <li key={index} className="flex items-start space-x-3">
                                        <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                                        <p className="text-gray-700">{suggestion}</p>
                                    </li>
                                ))}
                            </ul>
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
