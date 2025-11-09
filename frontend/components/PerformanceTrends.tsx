"use client";

import { useState, useEffect } from "react";
import dynamic from "next/dynamic";

// Dynamically import recharts to avoid SSR issues
const LineChart = dynamic(() => import('recharts').then(mod => mod.LineChart), { ssr: false });
const Line = dynamic(() => import('recharts').then(mod => mod.Line), { ssr: false });
const BarChart = dynamic(() => import('recharts').then(mod => mod.BarChart), { ssr: false });
const Bar = dynamic(() => import('recharts').then(mod => mod.Bar), { ssr: false });
const XAxis = dynamic(() => import('recharts').then(mod => mod.XAxis), { ssr: false });
const YAxis = dynamic(() => import('recharts').then(mod => mod.YAxis), { ssr: false });
const CartesianGrid = dynamic(() => import('recharts').then(mod => mod.CartesianGrid), { ssr: false });
const Tooltip = dynamic(() => import('recharts').then(mod => mod.Tooltip), { ssr: false });
const ResponsiveContainer = dynamic(() => import('recharts').then(mod => mod.ResponsiveContainer), { ssr: false });
const RadarChart = dynamic(() => import('recharts').then(mod => mod.RadarChart), { ssr: false });
const PolarGrid = dynamic(() => import('recharts').then(mod => mod.PolarGrid), { ssr: false });
const PolarAngleAxis = dynamic(() => import('recharts').then(mod => mod.PolarAngleAxis), { ssr: false });
const PolarRadiusAxis = dynamic(() => import('recharts').then(mod => mod.PolarRadiusAxis), { ssr: false });
const Radar = dynamic(() => import('recharts').then(mod => mod.Radar), { ssr: false });

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
    filler_word_percentage?: number;
    media_url: string;
    media_type?: string;
    original_filename?: string;
    created_at: string;
    duration_seconds?: number;
    words_per_minute?: number;
    syllables_per_minute?: number;
    pitch_mean?: number;
    pitch_std?: number;
    volume_mean?: number;
    volume_std?: number;
    analysis_data?: any;
    scores?: any;
    pause_events?: PauseEvent[];
    pitch_events?: PitchEvent[];
    speed_events?: SpeedEvent[];
    volume_events?: VolumeEvent[];
    filler_word_details?: {
        fillers: Record<string, number>;
        total_fillers: number;
        filler_percentage: number;
        word_count: number;
    };
    // CSSEF scores structure
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
}

interface Speech {
    id: string;
    title: string;
    description: string;
    context: string;
    goal: string;
    audience_description?: string;
    key_points?: string;
    self_improvement_goal?: string;
    with_context?: boolean;
    completed?: boolean;
    prpsa_score?: number;
    prpsa_completed: boolean;
    created_at?: string;
    updated_at?: string;
}

interface PerformanceTrendsProps {
    sessions: Session[];
    speech: Speech;
}

interface CSSEFTrendData {
    sessionNumber: number;
    sessionDate: string;
    sessionTitle: string;
    c1_topic_choice: number;
    c2_purpose: number;
    c3_supporting: number;
    c4_organization: number;
    c5_language: number;
    c6_vocal_variety: number;
    c7_pronunciation: number;
    overall_score?: number;
    filler_percentage: number;
    words_per_minute: number;
}

interface DeliveryTrendData {
    sessionNumber: number;
    sessionDate: string;
    sessionTitle: string;
    fillerPercentage: number;
    wordsPerMinute: number;
    pitchMean: number;
    volumeMean: number;
    pauseEventCount: number;
    speedEventCount: number;
}

const CSSEF_CRITERIA = [
    { key: 'c1_topic_choice', label: 'Topic Choice', color: '#8B5CF6' },
    { key: 'c2_purpose', label: 'Purpose', color: '#EF4444' },
    { key: 'c3_supporting', label: 'Supporting Materials', color: '#F59E0B' },
    { key: 'c4_organization', label: 'Organization', color: '#10B981' },
    { key: 'c5_language', label: 'Language Use', color: '#3B82F6' },
    { key: 'c6_vocal_variety', label: 'Vocal Variety', color: '#F97316' },
    { key: 'c7_pronunciation', label: 'Pronunciation', color: '#06B6D4' }
];

const PerformanceTrends: React.FC<PerformanceTrendsProps> = ({ sessions, speech }) => {
    const [activeTab, setActiveTab] = useState<'cssef' | 'delivery' | 'radar'>('cssef');

    // Process sessions data for CSSEF trends
    const processCSSEFTrendsData = (): CSSEFTrendData[] => {
        if (!sessions || sessions.length === 0) return [];

        // Sort sessions by creation date
        const sortedSessions = [...sessions].sort((a, b) => 
            new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
        );

        return sortedSessions.map((session, index) => {
            // Extract CSSEF scores from both new and legacy structures
            const getCSSEFScores = () => {
                const scores = {
                    c1_topic_choice: 0,
                    c2_purpose: 0,
                    c3_supporting: 0,
                    c4_organization: 0,
                    c5_language: 0,
                    c6_vocal_variety: 0,
                    c7_pronunciation: 0
                };

                // Check new cssef_scores structure first
                if (session.cssef_scores) {
                    Object.keys(scores).forEach(key => {
                        const scoreData = session.cssef_scores![key as keyof typeof session.cssef_scores];
                        scores[key as keyof typeof scores] = scoreData?.score || 0;
                    });
                } else {
                    // Check legacy direct properties structure
                    Object.keys(scores).forEach(key => {
                        const scoreData = session[key as keyof Session] as any;
                        scores[key as keyof typeof scores] = scoreData?.score || 0;
                    });
                }

                return scores;
            };

            const cssefScores = getCSSEFScores();
            
            return {
                sessionNumber: index + 1,
                sessionDate: new Date(session.created_at).toLocaleDateString('en-US', { 
                    month: 'short', 
                    day: 'numeric' 
                }),
                sessionTitle: session.title || `Session ${index + 1}`,
                ...cssefScores,
                overall_score: session.overall_score,
                filler_percentage: session.filler_word_percentage || (session.filler_word_details?.filler_percentage) || 0,
                words_per_minute: session.words_per_minute || 0
            };
        });
    };

    // Process delivery metrics data
    const processDeliveryTrendsData = (): DeliveryTrendData[] => {
        if (!sessions || sessions.length === 0) return [];

        const sortedSessions = [...sessions].sort((a, b) => 
            new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
        );

        return sortedSessions.map((session, index) => ({
            sessionNumber: index + 1,
            sessionDate: new Date(session.created_at).toLocaleDateString('en-US', { 
                month: 'short', 
                day: 'numeric' 
            }),
            sessionTitle: session.title || `Session ${index + 1}`,
            fillerPercentage: session.filler_word_percentage || (session.filler_word_details?.filler_percentage) || 0,
            wordsPerMinute: session.words_per_minute || 0,
            pitchMean: session.pitch_mean || 0,
            volumeMean: session.volume_mean || 0,
            pauseEventCount: session.pause_events?.length || 0,
            speedEventCount: session.speed_events?.length || 0
        }));
    };

    // Process radar chart data for latest session
    const processRadarData = () => {
        if (!sessions || sessions.length === 0) return [];

        const latestSession = sessions.reduce((latest, session) => 
            new Date(session.created_at) > new Date(latest.created_at) ? session : latest
        );

        const getCSSEFScores = (session: Session) => {
            const scores = {
                c1_topic_choice: 0,
                c2_purpose: 0,
                c3_supporting: 0,
                c4_organization: 0,
                c5_language: 0,
                c6_vocal_variety: 0,
                c7_pronunciation: 0
            };

            if (session.cssef_scores) {
                Object.keys(scores).forEach(key => {
                    const scoreData = session.cssef_scores![key as keyof typeof session.cssef_scores];
                    scores[key as keyof typeof scores] = scoreData?.score || 0;
                });
            } else {
                Object.keys(scores).forEach(key => {
                    const scoreData = session[key as keyof Session] as any;
                    scores[key as keyof typeof scores] = scoreData?.score || 0;
                });
            }

            return scores;
        };

        const scores = getCSSEFScores(latestSession);

        return CSSEF_CRITERIA.map(criterion => ({
            criterion: criterion.label,
            score: scores[criterion.key as keyof typeof scores],
            fullMark: 5
        }));
    };

    const cssefTrendsData = processCSSEFTrendsData();
    const deliveryTrendsData = processDeliveryTrendsData();
    const radarData = processRadarData();

    // Custom tooltip for CSSEF trends
    const CSSEFTooltip = ({ active, payload, label }: any) => {
        if (active && payload && payload.length > 0) {
            const sessionData = cssefTrendsData.find(d => d.sessionNumber.toString() === label);
            return (
                <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-4 max-w-xs">
                    <h4 className="font-semibold text-gray-900 mb-2">
                        {sessionData?.sessionTitle}
                    </h4>
                    <p className="text-sm text-gray-600 mb-2">{sessionData?.sessionDate}</p>
                    {payload.map((entry: any, index: number) => (
                        <div key={index} className="flex items-center justify-between">
                            <span className="text-xs" style={{ color: entry.color }}>
                                {entry.name}:
                            </span>
                            <span className="text-xs font-medium ml-2">
                                {entry.value?.toFixed(1)}/5
                            </span>
                        </div>
                    ))}
                </div>
            );
        }
        return null;
    };

    // Custom tooltip for delivery metrics
    const DeliveryTooltip = ({ active, payload, label }: any) => {
        if (active && payload && payload.length > 0) {
            const sessionData = deliveryTrendsData.find(d => d.sessionNumber.toString() === label);
            return (
                <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-4 max-w-xs">
                    <h4 className="font-semibold text-gray-900 mb-2">
                        {sessionData?.sessionTitle}
                    </h4>
                    <p className="text-sm text-gray-600 mb-2">{sessionData?.sessionDate}</p>
                    {payload.map((entry: any, index: number) => (
                        <div key={index} className="flex items-center justify-between">
                            <span className="text-xs" style={{ color: entry.color }}>
                                {entry.name}:
                            </span>
                            <span className="text-xs font-medium ml-2">
                                {entry.value?.toFixed(1)}
                                {entry.dataKey === 'fillerPercentage' ? '%' : 
                                 entry.dataKey === 'wordsPerMinute' ? ' wpm' : 
                                 entry.dataKey === 'pitchMean' ? ' Hz' :
                                 entry.dataKey === 'volumeMean' ? ' dB' : ''}
                            </span>
                        </div>
                    ))}
                </div>
            );
        }
        return null;
    };

    if (!sessions || sessions.length === 0) {
        return (
            <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-8">
                <div className="text-center py-12">
                    <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                        </svg>
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">No Performance Data</h3>
                    <p className="text-gray-500">Record some sessions to see performance trends and analytics</p>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
            {/* Header */}
            <div className="border-b border-gray-200 p-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                            <span className="w-8 h-8 bg-purple-500 text-white rounded-full flex items-center justify-center text-sm mr-3">📈</span>
                            Performance Trends
                        </h2>
                        <p className="text-gray-600 mt-1">
                            Track your improvement across {sessions.length} session{sessions.length !== 1 ? 's' : ''}
                        </p>
                    </div>
                    {speech.prpsa_completed && speech.prpsa_score && (
                        <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-2">
                            <div className="text-sm text-blue-700">PRPSA Score</div>
                            <div className="text-xl font-bold text-blue-900">{speech.prpsa_score}/170</div>
                            <div className="text-xs text-blue-600">
                                {speech.prpsa_score <= 34 ? 'Low Anxiety' :
                                 speech.prpsa_score <= 84 ? 'Moderate Anxiety' :
                                 speech.prpsa_score <= 134 ? 'High Anxiety' : 'Very High Anxiety'}
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Tabs */}
            <div className="border-b border-gray-200">
                <nav className="flex">
                    <button
                        onClick={() => setActiveTab('cssef')}
                        className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                            activeTab === 'cssef'
                                ? 'border-purple-500 text-purple-600 bg-purple-50'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                        }`}
                    >
                        CSSEF Competencies
                    </button>
                    <button
                        onClick={() => setActiveTab('delivery')}
                        className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                            activeTab === 'delivery'
                                ? 'border-blue-500 text-blue-600 bg-blue-50'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                        }`}
                    >
                        Delivery Metrics
                    </button>
                    <button
                        onClick={() => setActiveTab('radar')}
                        className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                            activeTab === 'radar'
                                ? 'border-green-500 text-green-600 bg-green-50'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                        }`}
                    >
                        Latest Performance
                    </button>
                </nav>
            </div>

            {/* Chart Content */}
            <div className="p-6">
                {activeTab === 'cssef' && (
                    <div>
                        <div className="mb-4">
                            <h3 className="text-lg font-semibold text-gray-900 mb-2">
                                CSSEF Competency Scores Over Time
                            </h3>
                            <p className="text-sm text-gray-600">
                                Track improvements in each speaking competency across sessions (1-5 scale)
                            </p>
                        </div>
                        
                        <div className="h-96 mb-6">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={cssefTrendsData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis 
                                        dataKey="sessionNumber" 
                                        tickFormatter={(value) => `Session ${value}`}
                                    />
                                    <YAxis domain={[0, 5]} />
                                    <Tooltip content={<CSSEFTooltip />} />
                                    {CSSEF_CRITERIA.map(criterion => (
                                        <Line
                                            key={criterion.key}
                                            type="monotone"
                                            dataKey={criterion.key}
                                            stroke={criterion.color}
                                            strokeWidth={2}
                                            name={criterion.label}
                                            connectNulls={false}
                                        />
                                    ))}
                                </LineChart>
                            </ResponsiveContainer>
                        </div>

                        {/* Score improvement summary */}
                        <div className="mb-6">
                            <h4 className="text-md font-medium text-gray-800 mb-3">
                                Progress Summary
                            </h4>
                            <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-4 mb-4">
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
                                    <div>
                                        <div className="text-2xl font-bold text-blue-600">
                                            {sessions.length}
                                        </div>
                                        <div className="text-sm text-blue-700">Total Sessions</div>
                                    </div>
                                    <div>
                                        <div className="text-2xl font-bold text-purple-600">
                                            {(() => {
                                                const validScores = cssefTrendsData.filter(d => d.overall_score).map(d => d.overall_score!);
                                                return validScores.length > 0 ? 
                                                    ((validScores.reduce((sum, score) => sum + score, 0) / validScores.length) / 5 * 100).toFixed(0) + '%'
                                                    : 'N/A';
                                            })()}
                                        </div>
                                        <div className="text-sm text-purple-700">Average Performance</div>
                                    </div>
                                    <div>
                                        <div className="text-2xl font-bold text-green-600">
                                            {(() => {
                                                const scores = cssefTrendsData.map(d => {
                                                    const criteriaScores = CSSEF_CRITERIA.map(c => d[c.key as keyof CSSEFTrendData] as number).filter(s => s > 0);
                                                    return criteriaScores.length > 0 ? criteriaScores.reduce((sum, s) => sum + s, 0) / criteriaScores.length : 0;
                                                });
                                                if (scores.length < 2) return 'N/A';
                                                const improvement = scores[scores.length - 1] - scores[0];
                                                return improvement > 0 ? `+${improvement.toFixed(1)}` : improvement.toFixed(1);
                                            })()}
                                        </div>
                                        <div className="text-sm text-green-700">Overall Improvement</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        {/* Detailed competency breakdown */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            {CSSEF_CRITERIA.map(criterion => {
                                const scores = cssefTrendsData.map(d => d[criterion.key as keyof CSSEFTrendData] as number);
                                const firstScore = scores[0] || 0;
                                const lastScore = scores[scores.length - 1] || 0;
                                const improvement = lastScore - firstScore;
                                
                                return (
                                    <div key={criterion.key} className="bg-gray-50 rounded-lg p-3 text-center">
                                        <div className="text-sm font-medium text-gray-700 mb-1">
                                            {criterion.label}
                                        </div>
                                        <div className="text-2xl font-bold" style={{ color: criterion.color }}>
                                            {lastScore.toFixed(1)}
                                        </div>
                                        <div className={`text-xs ${
                                            improvement > 0 ? 'text-green-600' :
                                            improvement < 0 ? 'text-red-600' : 'text-gray-500'
                                        }`}>
                                            {improvement > 0 ? '+' : ''}{improvement.toFixed(1)} overall
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}

                {activeTab === 'delivery' && (
                    <div>
                        <div className="mb-4">
                            <h3 className="text-lg font-semibold text-gray-900 mb-2">
                                Delivery Metrics Over Time
                            </h3>
                            <p className="text-sm text-gray-600">
                                Monitor speaking pace, filler words, and prosodic features across sessions
                            </p>
                        </div>

                        <div className="space-y-8">
                            {/* Filler Words and Speaking Rate */}
                            <div className="h-80">
                                <h4 className="text-md font-medium text-gray-800 mb-3">
                                    Speaking Quality Metrics
                                </h4>
                                <ResponsiveContainer width="100%" height="100%">
                                    <LineChart data={deliveryTrendsData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis 
                                            dataKey="sessionNumber" 
                                            tickFormatter={(value) => `Session ${value}`}
                                        />
                                        <YAxis yAxisId="left" />
                                        <YAxis yAxisId="right" orientation="right" />
                                        <Tooltip content={<DeliveryTooltip />} />
                                        <Line
                                            yAxisId="left"
                                            type="monotone"
                                            dataKey="fillerPercentage"
                                            stroke="#EF4444"
                                            strokeWidth={2}
                                            name="Filler Words (%)"
                                        />
                                        <Line
                                            yAxisId="right"
                                            type="monotone"
                                            dataKey="wordsPerMinute"
                                            stroke="#10B981"
                                            strokeWidth={2}
                                            name="Words per Minute"
                                        />
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>

                            {/* Prosodic Features */}
                            <div className="h-80">
                                <h4 className="text-md font-medium text-gray-800 mb-3">
                                    Prosodic Features
                                </h4>
                                <ResponsiveContainer width="100%" height="100%">
                                    <LineChart data={deliveryTrendsData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis 
                                            dataKey="sessionNumber" 
                                            tickFormatter={(value) => `Session ${value}`}
                                        />
                                        <YAxis yAxisId="left" />
                                        <YAxis yAxisId="right" orientation="right" />
                                        <Tooltip content={<DeliveryTooltip />} />
                                        <Line
                                            yAxisId="left"
                                            type="monotone"
                                            dataKey="pitchMean"
                                            stroke="#8B5CF6"
                                            strokeWidth={2}
                                            name="Mean Pitch (Hz)"
                                        />
                                        <Line
                                            yAxisId="right"
                                            type="monotone"
                                            dataKey="volumeMean"
                                            stroke="#F59E0B"
                                            strokeWidth={2}
                                            name="Mean Volume (dB)"
                                        />
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>

                            {/* Event Counts */}
                            <div className="h-80">
                                <h4 className="text-md font-medium text-gray-800 mb-3">
                                    Speech Event Frequency
                                </h4>
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={deliveryTrendsData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis 
                                            dataKey="sessionNumber" 
                                            tickFormatter={(value) => `S${value}`}
                                        />
                                        <YAxis />
                                        <Tooltip content={<DeliveryTooltip />} />
                                        <Bar dataKey="pauseEventCount" fill="#06B6D4" name="Pause Events" />
                                        <Bar dataKey="speedEventCount" fill="#F97316" name="Speed Variations" />
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                        </div>

                        {/* Metrics summary */}
                        <div className="mb-6">
                            <h4 className="text-md font-medium text-gray-800 mb-3">
                                Delivery Improvement Trends
                            </h4>
                            <div className="bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-lg p-4 mb-4">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="text-center">
                                        <div className="text-lg font-bold text-red-600">
                                            {(() => {
                                                const fillerRates = deliveryTrendsData.map(d => d.fillerPercentage).filter(r => r !== undefined);
                                                if (fillerRates.length < 2) return 'N/A';
                                                const trend = fillerRates[fillerRates.length - 1] - fillerRates[0];
                                                return trend < 0 ? `${trend.toFixed(1)}%` : `+${trend.toFixed(1)}%`;
                                            })()}
                                        </div>
                                        <div className="text-sm text-gray-700">Filler Word Change</div>
                                        <div className="text-xs text-gray-500">
                                            {(() => {
                                                const fillerRates = deliveryTrendsData.map(d => d.fillerPercentage).filter(r => r !== undefined);
                                                if (fillerRates.length < 2) return '';
                                                const trend = fillerRates[fillerRates.length - 1] - fillerRates[0];
                                                return trend < 0 ? '📈 Improving' : trend > 0 ? '📉 Needs Work' : '➡️ Stable';
                                            })()}
                                        </div>
                                    </div>
                                    <div className="text-center">
                                        <div className="text-lg font-bold text-green-600">
                                            {(() => {
                                                const wpmRates = deliveryTrendsData.map(d => d.wordsPerMinute).filter(r => r !== undefined && r > 0);
                                                if (wpmRates.length < 2) return 'N/A';
                                                const trend = wpmRates[wpmRates.length - 1] - wpmRates[0];
                                                return trend > 0 ? `+${trend.toFixed(0)}` : trend.toFixed(0);
                                            })()}
                                        </div>
                                        <div className="text-sm text-gray-700">Speaking Rate Change</div>
                                        <div className="text-xs text-gray-500">
                                            {(() => {
                                                const wpmRates = deliveryTrendsData.map(d => d.wordsPerMinute).filter(r => r !== undefined && r > 0);
                                                if (wpmRates.length < 2) return '';
                                                const trend = wpmRates[wpmRates.length - 1] - wpmRates[0];
                                                return trend > 0 ? '📈 Faster' : trend < 0 ? '📉 Slower' : '➡️ Stable';
                                            })()}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mt-6">
                            {[
                                { label: 'Latest Filler Rate', value: `${deliveryTrendsData[deliveryTrendsData.length - 1]?.fillerPercentage?.toFixed(1)}%`, color: 'text-red-600' },
                                { label: 'Latest Speaking Rate', value: `${deliveryTrendsData[deliveryTrendsData.length - 1]?.wordsPerMinute?.toFixed(0)} wpm`, color: 'text-green-600' },
                                { label: 'Latest Pitch', value: `${deliveryTrendsData[deliveryTrendsData.length - 1]?.pitchMean?.toFixed(0)} Hz`, color: 'text-purple-600' },
                                { label: 'Latest Volume', value: `${deliveryTrendsData[deliveryTrendsData.length - 1]?.volumeMean?.toFixed(0)} dB`, color: 'text-yellow-600' },
                                { label: 'Recent Pause Events', value: `${deliveryTrendsData[deliveryTrendsData.length - 1]?.pauseEventCount || 0}`, color: 'text-blue-600' },
                                { label: 'Recent Speed Changes', value: `${deliveryTrendsData[deliveryTrendsData.length - 1]?.speedEventCount || 0}`, color: 'text-orange-600' }
                            ].map((metric, index) => (
                                <div key={index} className="bg-gray-50 rounded-lg p-3 text-center">
                                    <div className="text-sm font-medium text-gray-700 mb-1">
                                        {metric.label}
                                    </div>
                                    <div className={`text-2xl font-bold ${metric.color}`}>
                                        {metric.value}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {activeTab === 'radar' && (
                    <div>
                        <div className="mb-4">
                            <h3 className="text-lg font-semibold text-gray-900 mb-2">
                                Latest Session Performance Profile
                            </h3>
                            <p className="text-sm text-gray-600">
                                Comprehensive view of your most recent session's CSSEF competency scores
                            </p>
                        </div>

                        <div className="flex justify-center">
                            <div className="h-96 w-full max-w-md">
                                <ResponsiveContainer width="100%" height="100%">
                                    <RadarChart data={radarData}>
                                        <PolarGrid />
                                        <PolarAngleAxis dataKey="criterion" type="category" scale="auto" reversed={false} />
                                        <PolarRadiusAxis domain={[0, 5]} axisLine={false} tick={false} />
                                        <Radar
                                            name="Score"
                                            dataKey="score"
                                            stroke="#8B5CF6"
                                            fill="#8B5CF6"
                                            fillOpacity={0.3}
                                            strokeWidth={2}
                                        />
                                        <Tooltip 
                                            formatter={(value: any) => [`${value}/5`, 'Score']}
                                            labelFormatter={(label) => `${label}`}
                                        />
                                    </RadarChart>
                                </ResponsiveContainer>
                            </div>
                        </div>

                        {/* Score breakdown */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
                            {radarData.map((item, index) => (
                                <div key={index} className="bg-gray-50 rounded-lg p-3 text-center">
                                    <div className="text-sm font-medium text-gray-700 mb-1">
                                        {item.criterion}
                                    </div>
                                    <div className="text-2xl font-bold text-purple-600">
                                        {item.score.toFixed(1)}
                                    </div>
                                    <div className="text-xs text-gray-500">
                                        out of 5
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default PerformanceTrends;