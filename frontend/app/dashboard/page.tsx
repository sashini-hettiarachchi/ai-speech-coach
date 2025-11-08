"use client";

import Image from "next/image";
import { useRef, useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from 'next/navigation';
import { Toaster, toast } from "react-hot-toast";
import LoadingDots from "../../components/LoadingDots";
import { sessionApi, speechApi } from "../../lib/api";
import ReactMarkdown from "react-markdown";
import dynamicImport from "next/dynamic";
import Link from "next/link";
import { useUser } from "@auth0/nextjs-auth0/client";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  RadialLinearScale,
  ArcElement,
} from 'chart.js';
import { Line, Bar, Radar, Doughnut } from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  RadialLinearScale,
  ArcElement,
);

// Force dynamic rendering
export const dynamic = 'force-dynamic';

const FillerWordsChart = dynamicImport(() => import("../../components/FillerWordsCharts"), { ssr: false });
const DeliveryMetricsTable = dynamicImport(() => import("../../components/DeliveryMetrics"), { ssr: false });

// CSSEF Score Utilities
interface CSSEFScores {
  c1_topic_choice_score?: number;
  c2_purpose_score?: number;
  c3_supporting_score?: number;
  c4_organization_score?: number;
  c5_language_score?: number;
  c6_vocal_variety_score?: number;
  c7_pronunciation_score?: number;
  overall_score?: number;
}

interface SessionWithScores {
  id: string;
  speechTitle: string;
  speechContext: string;
  created_at: string;
  duration_seconds?: number;
  words_per_minute?: number;
  filler_word_percentage?: number;
  speech_id: string;
  scores?: CSSEFScores;
  [key: string]: any;
}

interface SpeechWithStats {
  id: string;
  title: string;
  context: string;
  description: string;
  sessionCount: number;
  avgOverallScore?: number;
  latestScore?: number;
  improvement?: number;
  cssefScores?: CSSEFScores;
  prpsa_completed?: boolean;
  prpsa_score?: number;
}

const getCSSEFCompetencies = () => [
  { key: 'c1_topic_choice_score', label: 'Topic Choice', shortLabel: 'Topic' },
  { key: 'c2_purpose_score', label: 'Purpose & Thesis', shortLabel: 'Purpose' },
  { key: 'c3_supporting_score', label: 'Supporting Material', shortLabel: 'Support' },
  { key: 'c4_organization_score', label: 'Organization', shortLabel: 'Structure' },
  { key: 'c5_language_score', label: 'Language Use', shortLabel: 'Language' },
  { key: 'c6_vocal_variety_score', label: 'Vocal Variety', shortLabel: 'Delivery' },
  { key: 'c7_pronunciation_score', label: 'Pronunciation', shortLabel: 'Pronunciation' }
];

const calculateAverageScores = (sessions: SessionWithScores[]): CSSEFScores => {
  if (sessions.length === 0) return {};
  
  const competencies = getCSSEFCompetencies();
  const averages: CSSEFScores = {};
  
  competencies.forEach(comp => {
    const scores = sessions
      .map(s => s.scores?.[comp.key as keyof CSSEFScores])
      .filter((score): score is number => typeof score === 'number');
    
    if (scores.length > 0) {
      averages[comp.key as keyof CSSEFScores] = 
        Math.round((scores.reduce((sum, score) => sum + score, 0) / scores.length) * 10) / 10;
    }
  });
  
  // Calculate overall average
  const overallScores = sessions
    .map(s => s.scores?.overall_score)
    .filter((score): score is number => typeof score === 'number');
  
  if (overallScores.length > 0) {
    averages.overall_score = 
      Math.round((overallScores.reduce((sum, score) => sum + score, 0) / overallScores.length) * 10) / 10;
  }
  
  return averages;
};

const calculateImprovement = (sessions: SessionWithScores[]): number => {
  if (sessions.length < 2) return 0;
  
  const sortedSessions = sessions
    .filter(s => s.scores?.overall_score)
    .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
  
  if (sortedSessions.length < 2) return 0;
  
  const firstScore = sortedSessions[0].scores?.overall_score || 0;
  const lastScore = sortedSessions[sortedSessions.length - 1].scores?.overall_score || 0;
  
  return Math.round((lastScore - firstScore) * 10) / 10;
};

const getScoreColor = (score: number): string => {
  if (score >= 80) return 'text-green-600 bg-green-100';
  if (score >= 70) return 'text-blue-600 bg-blue-100';
  if (score >= 60) return 'text-yellow-600 bg-yellow-100';
  if (score >= 50) return 'text-orange-600 bg-orange-100';
  return 'text-red-600 bg-red-100';
};

const getImprovementColor = (improvement: number): string => {
  if (improvement > 5) return 'text-green-600';
  if (improvement > 0) return 'text-blue-600';
  if (improvement === 0) return 'text-gray-600';
  return 'text-red-600';
};

const getImprovementIcon = (improvement: number) => {
  if (improvement > 0) {
    return (
      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M3.293 9.707a1 1 0 010-1.414l6-6a1 1 0 011.414 0l6 6a1 1 0 01-1.414 1.414L11 5.414V17a1 1 0 11-2 0V5.414L4.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
      </svg>
    );
  } else if (improvement < 0) {
    return (
      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M16.707 10.293a1 1 0 010 1.414l-6 6a1 1 0 01-1.414 0l-6-6a1 1 0 111.414-1.414L9 14.586V3a1 1 0 012 0v11.586l4.293-4.293a1 1 0 011.414 0z" clipRule="evenodd" />
      </svg>
    );
  }
  return (
    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
      <path fillRule="evenodd" d="M3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
    </svg>
  );
};

// Chart Components
interface OverallScoreChartProps {
  speeches: SpeechWithStats[];
  sessions: SessionWithScores[];
}

const OverallScoreChart: React.FC<OverallScoreChartProps> = ({ speeches, sessions }) => {
  // Create data for overall score progression across all sessions
  const sortedSessions = sessions
    .filter(s => s.scores?.overall_score)
    .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());

  const data = {
    labels: sortedSessions.map((session, index) => `Session ${index + 1}`),
    datasets: [
      {
        label: 'Overall Score',
        data: sortedSessions.map(s => s.scores?.overall_score || 0),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 3,
        fill: true,
        tension: 0.4,
        pointBackgroundColor: 'rgb(59, 130, 246)',
        pointBorderColor: 'white',
        pointBorderWidth: 2,
        pointRadius: 6,
      }
    ]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: true,
        text: 'Overall Score Progression',
        font: {
          size: 16,
          weight: 'bold' as const,
        },
        color: '#1f2937',
      },
      tooltip: {
        callbacks: {
          afterLabel: (context: any) => {
            const session = sortedSessions[context.dataIndex];
            return [`Speech: ${session.speechTitle}`, `Date: ${new Date(session.created_at).toLocaleDateString()}`];
          }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
        ticks: {
          callback: (value: any) => `${value}%`,
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.1)',
        }
      },
      x: {
        grid: {
          display: false,
        }
      }
    }
  };

  return <Line data={data} options={options} />;
};

interface CSSEFRadarChartProps {
  sessions: SessionWithScores[];
}

const CSSEFRadarChart: React.FC<CSSEFRadarChartProps> = ({ sessions }) => {
  const competencies = getCSSEFCompetencies();
  
  // Calculate average scores for each competency
  const averageScores = competencies.map(comp => {
    const scores = sessions
      .map(s => s.scores?.[comp.key as keyof CSSEFScores])
      .filter((score): score is number => typeof score === 'number');
    
    return scores.length > 0 
      ? scores.reduce((sum, score) => sum + score, 0) / scores.length 
      : 0;
  });

  const data = {
    labels: competencies.map(c => c.shortLabel),
    datasets: [
      {
        label: 'Average CSSEF Scores',
        data: averageScores,
        backgroundColor: 'rgba(34, 197, 94, 0.2)',
        borderColor: 'rgb(34, 197, 94)',
        borderWidth: 3,
        pointBackgroundColor: 'rgb(34, 197, 94)',
        pointBorderColor: 'white',
        pointBorderWidth: 2,
        pointRadius: 6,
      }
    ]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: true,
        text: 'CSSEF Competency Radar',
        font: {
          size: 16,
          weight: 'bold' as const,
        },
        color: '#1f2937',
      }
    },
    scales: {
      r: {
        beginAtZero: true,
        max: 100,
        ticks: {
          callback: (value: any) => `${value}%`,
          stepSize: 20,
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.1)',
        },
        angleLines: {
          color: 'rgba(0, 0, 0, 0.1)',
        }
      }
    }
  };

  return <Radar data={data} options={options} />;
};

interface SpeechComparisonChartProps {
  speeches: SpeechWithStats[];
}

const SpeechComparisonChart: React.FC<SpeechComparisonChartProps> = ({ speeches }) => {
  const speechesWithScores = speeches.filter(s => s.avgOverallScore);
  
  const data = {
    labels: speechesWithScores.map(s => s.title.length > 15 ? s.title.substring(0, 15) + '...' : s.title),
    datasets: [
      {
        label: 'Average Score',
        data: speechesWithScores.map(s => s.avgOverallScore || 0),
        backgroundColor: speechesWithScores.map(s => {
          const score = s.avgOverallScore || 0;
          if (score >= 80) return 'rgba(34, 197, 94, 0.8)';
          if (score >= 70) return 'rgba(59, 130, 246, 0.8)';
          if (score >= 60) return 'rgba(234, 179, 8, 0.8)';
          if (score >= 50) return 'rgba(249, 115, 22, 0.8)';
          return 'rgba(239, 68, 68, 0.8)';
        }),
        borderColor: speechesWithScores.map(s => {
          const score = s.avgOverallScore || 0;
          if (score >= 80) return 'rgb(34, 197, 94)';
          if (score >= 70) return 'rgb(59, 130, 246)';
          if (score >= 60) return 'rgb(234, 179, 8)';
          if (score >= 50) return 'rgb(249, 115, 22)';
          return 'rgb(239, 68, 68)';
        }),
        borderWidth: 2,
      }
    ]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: true,
        text: 'Speech Performance Comparison',
        font: {
          size: 16,
          weight: 'bold' as const,
        },
        color: '#1f2937',
      },
      tooltip: {
        callbacks: {
          afterLabel: (context: any) => {
            const speech = speechesWithScores[context.dataIndex];
            return [
              `Sessions: ${speech.sessionCount}`,
              `Improvement: ${speech.improvement ? (speech.improvement > 0 ? '+' : '') + speech.improvement + '%' : 'N/A'}`
            ];
          }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
        ticks: {
          callback: (value: any) => `${value}%`,
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.1)',
        }
      },
      x: {
        grid: {
          display: false,
        }
      }
    }
  };

  return <Bar data={data} options={options} />;
};

interface PSAProgressChartProps {
  speeches: SpeechWithStats[];
  sessions: SessionWithScores[];
}

const PSAProgressChart: React.FC<PSAProgressChartProps> = ({ speeches, sessions }) => {
  const speechesWithPSA = speeches.filter(s => s.prpsa_completed && s.prpsa_score);
  
  if (speechesWithPSA.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg">
        <div className="text-center">
          <p className="text-gray-500 mb-2">No PSA data available</p>
          <p className="text-sm text-gray-400">Complete PRPSA assessments to see anxiety tracking</p>
        </div>
      </div>
    );
  }

  // Create correlation data between practice sessions and PSA scores
  const correlationData = speechesWithPSA.map(speech => {
    const speechSessions = sessions.filter(s => s.speech_id === speech.id);
    return {
      speechTitle: speech.title,
      sessionCount: speechSessions.length,
      psaScore: speech.prpsa_score || 0,
      avgOverallScore: speech.avgOverallScore || 0
    };
  });

  const data = {
    labels: correlationData.map(d => d.speechTitle.length > 10 ? d.speechTitle.substring(0, 10) + '...' : d.speechTitle),
    datasets: [
      {
        label: 'PSA Score',
        data: correlationData.map(d => d.psaScore),
        backgroundColor: 'rgba(147, 51, 234, 0.8)',
        borderColor: 'rgb(147, 51, 234)',
        borderWidth: 2,
        yAxisID: 'y',
      },
      {
        label: 'Session Count',
        data: correlationData.map(d => d.sessionCount),
        backgroundColor: 'rgba(34, 197, 94, 0.8)',
        borderColor: 'rgb(34, 197, 94)',
        borderWidth: 2,
        yAxisID: 'y1',
      }
    ]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'PSA Scores vs Practice Sessions',
        font: {
          size: 16,
          weight: 'bold' as const,
        },
        color: '#1f2937',
      }
    },
    scales: {
      y: {
        type: 'linear' as const,
        display: true,
        position: 'left' as const,
        title: {
          display: true,
          text: 'PSA Score',
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.1)',
        }
      },
      y1: {
        type: 'linear' as const,
        display: true,
        position: 'right' as const,
        title: {
          display: true,
          text: 'Session Count',
        },
        grid: {
          drawOnChartArea: false,
        },
      },
      x: {
        grid: {
          display: false,
        }
      }
    }
  };

  return <Bar data={data} options={options} />;
};

interface SpeechOverviewChartProps {
  speeches: SpeechWithStats[];
}

const SpeechOverviewChart: React.FC<SpeechOverviewChartProps> = ({ speeches }) => {
  const data = {
    labels: speeches.map(s => s.title.length > 15 ? s.title.substring(0, 15) + '...' : s.title),
    datasets: [
      {
        label: 'Practice Sessions',
        data: speeches.map(s => s.sessionCount),
        backgroundColor: speeches.map(s => {
          const count = s.sessionCount;
          if (count >= 5) return 'rgba(34, 197, 94, 0.8)';
          if (count >= 3) return 'rgba(59, 130, 246, 0.8)';
          if (count >= 1) return 'rgba(234, 179, 8, 0.8)';
          return 'rgba(156, 163, 175, 0.8)';
        }),
        borderColor: speeches.map(s => {
          const count = s.sessionCount;
          if (count >= 5) return 'rgb(34, 197, 94)';
          if (count >= 3) return 'rgb(59, 130, 246)';
          if (count >= 1) return 'rgb(234, 179, 8)';
          return 'rgb(156, 163, 175)';
        }),
        borderWidth: 2,
      }
    ]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: true,
        text: 'Speech Practice Overview',
        font: {
          size: 16,
          weight: 'bold' as const,
        },
        color: '#1f2937',
      },
      tooltip: {
        callbacks: {
          afterLabel: (context: any) => {
            const speech = speeches[context.dataIndex];
            return [
              `Context: ${speech.context || 'None'}`,
              speech.sessionCount > 0 ? 'Click to start practicing!' : 'No sessions yet'
            ];
          }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          stepSize: 1,
          callback: (value: any) => `${value} sessions`,
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.1)',
        }
      },
      x: {
        grid: {
          display: false,
        }
      }
    }
  };

  return <Bar data={data} options={options} />;
};

interface MiniTrendChartProps {
  speechId: string;
  sessions: SessionWithScores[];
}

const MiniTrendChart: React.FC<MiniTrendChartProps> = ({ speechId, sessions }) => {
  const speechSessions = sessions
    .filter(s => s.speech_id === speechId && s.scores?.overall_score)
    .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());

  if (speechSessions.length < 2) {
    return null;
  }

  const data = {
    labels: speechSessions.map((_, index) => `S${index + 1}`),
    datasets: [
      {
        data: speechSessions.map(s => s.scores?.overall_score || 0),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 2,
        fill: true,
        tension: 0.4,
        pointRadius: 0,
        pointHoverRadius: 0,
      }
    ]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        enabled: false,
      }
    },
    scales: {
      x: {
        display: false,
      },
      y: {
        display: false,
        min: 0,
        max: 100,
      }
    },
    elements: {
      point: {
        radius: 0
      }
    }
  };

  return (
    <div className="h-8 w-full">
      <Line data={data} options={options} />
    </div>
  );
};

function DashboardContent() {
	const { user : currentUser, isLoading } = useUser();
	console.log("user", currentUser)
	const router = useRouter();
	const searchParams = useSearchParams();
	const [loading, setLoading] = useState(true);
	const [speeches, setSpeeches] = useState<SpeechWithStats[]>([]);
	const [sessions, setSessions] = useState<SessionWithScores[]>([]);
	const [dataLoaded, setDataLoaded] = useState(false); // Cache flag
	const [stats, setStats] = useState({
		totalSpeeches: 0,
		totalSessions: 0,
		totalPracticeTime: 0,
		avgFillerWordsRate: 0,
		avgOverallScore: 0,
		avgCSSEFScore: 0,
		totalImprovement: 0
	});


	useEffect(() => {
		if (!dataLoaded) {
			loadDashboardData();
		}
	}, [dataLoaded]);

	const loadDashboardData = async () => {
		try {
			setLoading(true);
			console.log("Starting dashboard data load...");
			
			// Load speeches
			const speechData = await speechApi.getSpeeches();
			console.log("Raw speech data:", speechData);
			
			// Handle different API response formats
			const speechesList = Array.isArray(speechData) ? speechData : (speechData.speeches || []);
			console.log("Processed speeches list:", speechesList);

			// Load all sessions for speeches that have session_count > 0
			let allSessions: SessionWithScores[] = [];
			let totalPracticeTime = 0;
			let totalFillerWords = 0;
			let sessionsWithFillerData = 0;
			let totalOverallScores = 0;
			let sessionsWithOverallScores = 0;
			let totalCSSEFScores = 0;
			let sessionsWithCSSEFScores = 0;

			// Process each speech and collect session data
			const processedSpeeches: SpeechWithStats[] = [];

			for (const speech of speechesList) {
				console.log(`Processing speech: ${speech.title} (ID: ${speech.id}, Sessions: ${speech.session_count})`);
				
				try {
					// Only fetch sessions if session_count > 0
					let sessionsWithSpeechInfo: SessionWithScores[] = [];
					
					if (speech.session_count && speech.session_count > 0) {
						console.log(`Getting detailed speech data for ${speech.id} with sessions...`);
						
						// Get detailed speech data which includes nested sessions
						const detailedSpeechResponse = await speechApi.getSpeech(speech.id);
						console.log(`Detailed speech response for ${speech.id}:`, detailedSpeechResponse);
						
						let speechWithSessions = null;
						if (detailedSpeechResponse && detailedSpeechResponse.speech) {
							speechWithSessions = detailedSpeechResponse.speech;
						} else if (detailedSpeechResponse) {
							speechWithSessions = detailedSpeechResponse;
						}
						
						if (speechWithSessions && speechWithSessions.sessions && Array.isArray(speechWithSessions.sessions)) {
							console.log(`Found ${speechWithSessions.sessions.length} sessions in speech data`);
							
							sessionsWithSpeechInfo = speechWithSessions.sessions.map((session: any) => ({
								...session,
								speechTitle: speech.title,
								speechContext: speech.context,
								scores: {
									// Extract CSSEF scores from the nested structure
									c1_topic_choice_score: session.cssef_scores?.c1_topic_choice?.score,
									c2_purpose_score: session.cssef_scores?.c2_purpose?.score,
									c3_supporting_score: session.cssef_scores?.c3_supporting?.score,
									c4_organization_score: session.cssef_scores?.c4_organization?.score,
									c5_language_score: session.cssef_scores?.c5_language?.score,
									c6_vocal_variety_score: session.cssef_scores?.c6_vocal_variety?.score,
									c7_pronunciation_score: session.cssef_scores?.c7_pronunciation?.score,
									overall_score: session.overall_score
								}
							}));
						} else {
							console.log(`No sessions found in detailed speech data for ${speech.id}`);
						}
						
						allSessions = [...allSessions, ...sessionsWithSpeechInfo];

						// Calculate stats for each session
						sessionsWithSpeechInfo.forEach((session) => {
							if (session.duration_seconds) {
								totalPracticeTime += session.duration_seconds;
							}
							if (session.filler_word_percentage !== undefined) {
								totalFillerWords += session.filler_word_percentage;
								sessionsWithFillerData++;
							}
							if (session.scores?.overall_score) {
								totalOverallScores += session.scores.overall_score;
								sessionsWithOverallScores++;
							}
							
							// Calculate average CSSEF scores for this session
							const competencies = getCSSEFCompetencies();
							const sessionCSSEFScores = competencies
								.map(comp => session.scores?.[comp.key as keyof CSSEFScores])
								.filter((score): score is number => typeof score === 'number');
							
							if (sessionCSSEFScores.length > 0) {
								totalCSSEFScores += sessionCSSEFScores.reduce((sum, score) => sum + score, 0) / sessionCSSEFScores.length;
								sessionsWithCSSEFScores++;
							}
						});
					}

					// Calculate speech-level statistics
					const avgScores = calculateAverageScores(sessionsWithSpeechInfo);
					const improvement = calculateImprovement(sessionsWithSpeechInfo);
					const latestSession = sessionsWithSpeechInfo.sort((a, b) => 
						new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
					)[0];

					processedSpeeches.push({
						...speech,
						sessionCount: speech.session_count || 0,
						avgOverallScore: avgScores.overall_score,
						latestScore: latestSession?.scores?.overall_score,
						improvement,
						cssefScores: avgScores
					});

				} catch (error) {
					console.error(`Error loading sessions for speech ${speech.id}:`, error);
					// Add speech with no sessions
					processedSpeeches.push({
						...speech,
						sessionCount: speech.session_count || 0
					});
				}
			}

			console.log("Processed speeches:", processedSpeeches);
			console.log("All sessions:", allSessions);

			setSessions(allSessions);
			setSpeeches(processedSpeeches);
			
			// Calculate total improvement across all speeches
			const totalImprovement = processedSpeeches
				.map(speech => speech.improvement || 0)
				.reduce((sum, imp) => sum + imp, 0);

			setStats({
				totalSpeeches: speechesList.length,
				totalSessions: allSessions.length,
				totalPracticeTime: Math.round(totalPracticeTime / 60), // Convert to minutes
				avgFillerWordsRate: sessionsWithFillerData > 0 ? 
					Math.round((totalFillerWords / sessionsWithFillerData) * 10) / 10 : 0,
				avgOverallScore: sessionsWithOverallScores > 0 ?
					Math.round((totalOverallScores / sessionsWithOverallScores) * 10) / 10 : 0,
				avgCSSEFScore: sessionsWithCSSEFScores > 0 ?
					Math.round((totalCSSEFScores / sessionsWithCSSEFScores) * 10) / 10 : 0,
				totalImprovement: Math.round(totalImprovement * 10) / 10
			});

			setDataLoaded(true); // Mark data as loaded
			console.log("Dashboard data loading completed successfully");

		} catch (error) {
			console.error("Error loading dashboard data:", error);
			toast.error("Failed to load dashboard data");
		} finally {
			setLoading(false);
		}
	};

	if (isLoading || loading) {
		return (
			<div className="flex justify-center items-center min-h-screen">
				<div className="text-lg">Loading dashboard...</div>
			</div>
		);
	}

	const formatDate = (dateString: string) => {
		return new Date(dateString).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
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

	return (
		<div className="flex max-w-6xl mx-auto flex-col py-2 min-h-screen">
			{/* User Profile Section */}
			{false && (
				<div className="w-full px-4 mt-12 sm:mt-20 mb-8">
					<div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
						<div className="flex items-center space-x-4">
							<div>
								<h2 className="text-2xl font-bold text-gray-900">
									Welcome back, User!
								</h2>
								<p className="text-gray-600">Demo Mode</p>
								<p className="text-sm text-orange-600 mt-1">
									Demo Mode - Auth0 not configured
								</p>
							</div>
						</div>
						
						{/* Quick Stats */}
						<div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6">
							<div className="bg-blue-50 rounded-lg p-4">
								<h3 className="text-sm font-medium text-blue-800 mb-1">Total Speeches</h3>
								<p className="text-2xl font-bold text-blue-900">{stats.totalSpeeches}</p>
							</div>
							<div className="bg-green-50 rounded-lg p-4">
								<h3 className="text-sm font-medium text-green-800 mb-1">Total Sessions</h3>
								<p className="text-2xl font-bold text-green-900">{stats.totalSessions}</p>
							</div>
							<div className="bg-purple-50 rounded-lg p-4">
								<h3 className="text-sm font-medium text-purple-800 mb-1">Practice Time</h3>
								<p className="text-2xl font-bold text-purple-900">{stats.totalPracticeTime}m</p>
							</div>
							<div className="bg-orange-50 rounded-lg p-4">
								<h3 className="text-sm font-medium text-orange-800 mb-1">Avg Filler Rate</h3>
								<p className="text-2xl font-bold text-orange-900">{stats.avgFillerWordsRate}%</p>
							</div>
						</div>
					</div>
				</div>
			)}

			<main className="flex flex-1 w-full flex-col px-4">
				<div className="max-w-6xl mx-auto w-full">
					<h1 className="text-4xl font-bold text-slate-900 mb-8 text-center">
						Speech Coach Dashboard
					</h1>

					{/* Quick Actions */}
					<div className="flex justify-center space-x-4 mb-8">
						<Link 
							href="/speeches/new"
							className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center space-x-2"
						>
							<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
							</svg>
							<span>New Speech</span>
						</Link>
						<Link 
							href="/speeches"
							className="bg-gray-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-gray-700 transition-colors flex items-center space-x-2"
						>
							<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
							</svg>
							<span>Quick Practice</span>
						</Link>
					</div>

					{/* Enhanced Stats Section */}
					<div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
						<h2 className="text-2xl font-bold text-gray-900 mb-6">Performance Overview</h2>
						
						<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
							<div className="bg-blue-50 rounded-lg p-4">
								<h3 className="text-sm font-medium text-blue-800 mb-1">Total Speeches</h3>
								<p className="text-2xl font-bold text-blue-900">{stats.totalSpeeches}</p>
								<p className="text-xs text-blue-600 mt-1">Created speeches</p>
							</div>
							<div className="bg-green-50 rounded-lg p-4">
								<h3 className="text-sm font-medium text-green-800 mb-1">Practice Sessions</h3>
								<p className="text-2xl font-bold text-green-900">{stats.totalSessions}</p>
								<p className="text-xs text-green-600 mt-1">{stats.totalPracticeTime}m total time</p>
							</div>
							<div className="bg-purple-50 rounded-lg p-4">
								<h3 className="text-sm font-medium text-purple-800 mb-1">Avg Overall Score</h3>
								<p className="text-2xl font-bold text-purple-900">
									{stats.avgOverallScore ? `${stats.avgOverallScore}%` : 'N/A'}
								</p>
								<p className="text-xs text-purple-600 mt-1">Across all sessions</p>
							</div>
							<div className="bg-orange-50 rounded-lg p-4">
								<h3 className="text-sm font-medium text-orange-800 mb-1">Total Improvement</h3>
								<div className="flex items-center space-x-1">
									<p className={`text-2xl font-bold ${getImprovementColor(stats.totalImprovement)}`}>
										{stats.totalImprovement > 0 ? '+' : ''}{stats.totalImprovement}%
									</p>
									<div className={getImprovementColor(stats.totalImprovement)}>
										{getImprovementIcon(stats.totalImprovement)}
									</div>
								</div>
								<p className="text-xs text-orange-600 mt-1">Combined progress</p>
							</div>
						</div>

						{/* CSSEF Competency Breakdown */}
						{stats.avgCSSEFScore > 0 && (
							<div className="border-t border-gray-200 pt-6">
								<h3 className="text-lg font-semibold text-gray-900 mb-4">CSSEF Competency Overview</h3>
								<div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
									{getCSSEFCompetencies().map(competency => {
										// Calculate average for this competency across all sessions
										const competencyScores = sessions
											.map(s => s.scores?.[competency.key as keyof CSSEFScores])
											.filter((score): score is number => typeof score === 'number');
										
										const avgScore = competencyScores.length > 0 
											? Math.round((competencyScores.reduce((sum, score) => sum + score, 0) / competencyScores.length) * 10) / 10
											: null;

										return avgScore ? (
											<div key={competency.key} className="text-center">
												<div className={`inline-flex items-center px-3 py-2 rounded-lg text-sm font-semibold ${getScoreColor(avgScore)}`}>
													{avgScore}%
												</div>
												<p className="text-xs text-gray-600 mt-2 font-medium">{competency.shortLabel}</p>
												<p className="text-xs text-gray-400">{competencyScores.length} sessions</p>
											</div>
										) : (
											<div key={competency.key} className="text-center">
												<div className="inline-flex items-center px-3 py-2 rounded-lg text-sm font-medium bg-gray-100 text-gray-500">
													N/A
												</div>
												<p className="text-xs text-gray-600 mt-2 font-medium">{competency.shortLabel}</p>
												<p className="text-xs text-gray-400">No data</p>
											</div>
										);
									})}
								</div>
							</div>
						)}

						{/* Speaking Anxiety Progress (if PSA data available) */}
						{speeches.some(s => s.prpsa_completed) && (
							<div className="border-t border-gray-200 pt-6 mt-6">
								<h3 className="text-lg font-semibold text-gray-900 mb-4">Speaking Anxiety Progress</h3>
								<div className="bg-purple-50 rounded-lg p-4">
									<div className="flex items-center justify-between">
										<div>
											<p className="text-sm font-medium text-purple-800">PSA Assessments Completed</p>
											<p className="text-2xl font-bold text-purple-900">
												{speeches.filter(s => s.prpsa_completed).length}
											</p>
										</div>
										<div className="text-right">
											<p className="text-sm text-purple-600">
												Practice sessions help reduce speaking anxiety
											</p>
											<p className="text-xs text-purple-500 mt-1">
												Complete PRPSA assessments to track progress
											</p>
										</div>
									</div>
								</div>
							</div>
						)}
					</div>

					{/* Performance Analytics Charts */}
					<div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
						<h2 className="text-2xl font-bold text-gray-900 mb-6">Performance Analytics</h2>
						
						{sessions.length > 0 ? (
							<>
								<div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
									{/* Overall Score Progression */}
									<div className="bg-gray-50 rounded-lg p-4">
										<div className="h-64">
											<OverallScoreChart speeches={speeches} sessions={sessions} />
										</div>
									</div>
									
									{/* Speech Comparison */}
									<div className="bg-gray-50 rounded-lg p-4">
										<div className="h-64">
											<SpeechComparisonChart speeches={speeches} />
										</div>
									</div>
								</div>
								
								<div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
									{/* CSSEF Competency Radar */}
									<div className="bg-gray-50 rounded-lg p-4">
										<div className="h-64">
											<CSSEFRadarChart sessions={sessions} />
										</div>
									</div>
									
									{/* PSA Progress Chart */}
									<div className="bg-gray-50 rounded-lg p-4">
										<div className="h-64">
											<PSAProgressChart speeches={speeches} sessions={sessions} />
										</div>
									</div>
								</div>
								
								{/* Chart Insights */}
								<div className="mt-6 border-t border-gray-200 pt-6">
									<h3 className="text-lg font-semibold text-gray-900 mb-4">Chart Insights</h3>
									<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
										<div className="bg-blue-50 rounded-lg p-3">
											<h4 className="text-sm font-semibold text-blue-900 mb-1">Score Trend</h4>
											<p className="text-xs text-blue-700">
												{sessions.length > 1 ? 
													`${sessions.length} sessions showing progression over time` :
													'Practice more to see trends'
												}
											</p>
										</div>
										<div className="bg-green-50 rounded-lg p-3">
											<h4 className="text-sm font-semibold text-green-900 mb-1">Best Competency</h4>
											<p className="text-xs text-green-700">
												{(() => {
													const competencies = getCSSEFCompetencies();
													const avgScores = competencies.map(comp => {
														const scores = sessions
															.map(s => s.scores?.[comp.key as keyof CSSEFScores])
															.filter((score): score is number => typeof score === 'number');
														return { 
															competency: comp, 
															avgScore: scores.length > 0 ? scores.reduce((sum, score) => sum + score, 0) / scores.length : 0 
														};
													});
													const best = avgScores.reduce((max, current) => current.avgScore > max.avgScore ? current : max);
													return best.avgScore > 0 ? `${best.competency.shortLabel} (${Math.round(best.avgScore)}%)` : 'Practice more to identify strengths';
												})()}
											</p>
										</div>
										<div className="bg-yellow-50 rounded-lg p-3">
											<h4 className="text-sm font-semibold text-yellow-900 mb-1">Focus Area</h4>
											<p className="text-xs text-yellow-700">
												{(() => {
													const competencies = getCSSEFCompetencies();
													const avgScores = competencies.map(comp => {
														const scores = sessions
															.map(s => s.scores?.[comp.key as keyof CSSEFScores])
															.filter((score): score is number => typeof score === 'number');
														return { 
															competency: comp, 
															avgScore: scores.length > 0 ? scores.reduce((sum, score) => sum + score, 0) / scores.length : 0 
														};
													}).filter(s => s.avgScore > 0);
													const lowest = avgScores.length > 0 ? avgScores.reduce((min, current) => current.avgScore < min.avgScore ? current : min) : null;
													return lowest ? `${lowest.competency.shortLabel} (${Math.round(lowest.avgScore)}%)` : 'All areas performing well';
												})()}
											</p>
										</div>
										<div className="bg-purple-50 rounded-lg p-3">
											<h4 className="text-sm font-semibold text-purple-900 mb-1">Practice Impact</h4>
											<p className="text-xs text-purple-700">
												{speeches.filter(s => s.improvement && s.improvement > 0).length > 0 ?
													`${speeches.filter(s => s.improvement && s.improvement > 0).length} speeches improving` :
													'Continue practicing for visible improvement'
												}
											</p>
										</div>
									</div>
								</div>
							</>
						) : speeches.length > 0 ? (
							/* Show Speech Overview Charts when no sessions but speeches exist */
							<div className="space-y-6">
								<div className="text-center py-6 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg">
									<div className="max-w-md mx-auto">
										<div className="w-16 h-16 mx-auto mb-4 bg-blue-100 rounded-full flex items-center justify-center">
											<svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
											</svg>
										</div>
										<h3 className="text-lg font-semibold text-gray-900 mb-2">Ready for Analytics!</h3>
										<p className="text-sm text-gray-600 mb-4">
											You have {speeches.length} speeches ready. Start practicing to see detailed performance charts and CSSEF competency tracking.
										</p>
										{speeches.filter(s => s.sessionCount > 0).length > 0 && (
											<p className="text-xs text-blue-600 mb-4">
												Some speeches have sessions - data loading in progress...
											</p>
										)}
										<div className="flex justify-center space-x-3 mt-4">
											<Link 
												href="/speeches/new"
												className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
											>
												Create Speech
											</Link>
											{speeches.length > 0 && (
												<Link 
													href={`/speeches/${speeches[0].id}/sessions/new`}
													className="bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-green-700 transition-colors"
												>
													Start Practicing
												</Link>
											)}
											<button
												onClick={() => {
													setDataLoaded(false);
													loadDashboardData();
												}}
												className="bg-gray-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-700 transition-colors"
											>
												Refresh Data
											</button>
										</div>

										{/* Debug Info */}
										<div className="mt-4 text-xs text-gray-500 bg-gray-50 rounded p-2">
											<p>Debug: Speeches: {speeches.length}, Sessions: {sessions.length}</p>
											{speeches.length > 0 && (
												<p>Speeches with sessions: {speeches.filter(s => s.sessionCount > 0).map(s => `${s.title} (${s.sessionCount})`).join(', ')}</p>
											)}
											{sessions.length > 0 && (
												<div>
													<p>Sample session CSSEF scores:</p>
													{sessions.slice(0, 1).map(session => (
														<div key={session.id} className="ml-2">
															<p>Session {session.session_number}: Overall Score {session.overall_score}</p>
															{session.scores && (
																<p>CSSEF: C1:{session.scores.c1_topic_choice_score} C2:{session.scores.c2_purpose_score} C3:{session.scores.c3_supporting_score}</p>
															)}
														</div>
													))}
												</div>
											)}
										</div>
									</div>
								</div>
								
								{/* Speech Overview Chart */}
								<div className="bg-gray-50 rounded-lg p-4">
									<div className="h-64">
										<SpeechOverviewChart speeches={speeches} />
									</div>
								</div>
							</div>
						) : (
							/* Empty State with Demo Charts */
							<div className="space-y-6">
								<div className="text-center py-8 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg">
									<div className="max-w-md mx-auto">
										<div className="w-16 h-16 mx-auto mb-4 bg-blue-100 rounded-full flex items-center justify-center">
											<svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
											</svg>
										</div>
										<h3 className="text-lg font-semibold text-gray-900 mb-2">Start Practicing to See Analytics</h3>
										<p className="text-sm text-gray-600 mb-4">
											Once you complete practice sessions, you'll see detailed charts showing your progress across CSSEF competencies, overall scores, and speaking anxiety reduction.
										</p>
										<div className="flex justify-center space-x-3">
											<Link 
												href="/speeches/new"
												className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
											>
												Create Speech
											</Link>
											{speeches.length > 0 && (
												<Link 
													href={`/speeches/${speeches[0].id}/sessions/new`}
													className="bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-green-700 transition-colors"
												>
													Start Practicing
												</Link>
											)}
										</div>
										
										{/* Add debug info */}
										<div className="mt-4 text-xs text-gray-500 bg-gray-50 rounded p-2">
											<p>Debug: Speeches: {speeches.length}, Sessions: {sessions.length}</p>
											{speeches.length > 0 && (
												<p>Speech titles: {speeches.map(s => s.title).join(', ')}</p>
											)}
										</div>
									</div>
								</div>
								
								{/* Preview of what charts will look like */}
								<div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
									<div className="bg-gray-50 rounded-lg p-4 relative">
										<div className="h-64 flex items-center justify-center">
											<div className="text-center">
												<div className="w-12 h-12 mx-auto mb-3 bg-gray-200 rounded-full flex items-center justify-center">
													<svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
														<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
													</svg>
												</div>
												<h4 className="text-sm font-medium text-gray-700 mb-1">Score Progress Chart</h4>
												<p className="text-xs text-gray-500">Track improvement over time</p>
											</div>
										</div>
									</div>
									<div className="bg-gray-50 rounded-lg p-4 relative">
										<div className="h-64 flex items-center justify-center">
											<div className="text-center">
												<div className="w-12 h-12 mx-auto mb-3 bg-gray-200 rounded-full flex items-center justify-center">
													<svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
														<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
													</svg>
												</div>
												<h4 className="text-sm font-medium text-gray-700 mb-1">Speech Comparison</h4>
												<p className="text-xs text-gray-500">Compare scores across speeches</p>
											</div>
										</div>
									</div>
									<div className="bg-gray-50 rounded-lg p-4 relative">
										<div className="h-64 flex items-center justify-center">
											<div className="text-center">
												<div className="w-12 h-12 mx-auto mb-3 bg-gray-200 rounded-full flex items-center justify-center">
													<svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
														<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
													</svg>
												</div>
												<h4 className="text-sm font-medium text-gray-700 mb-1">CSSEF Competencies</h4>
												<p className="text-xs text-gray-500">7 areas of speaking skills</p>
											</div>
										</div>
									</div>
									<div className="bg-gray-50 rounded-lg p-4 relative">
										<div className="h-64 flex items-center justify-center">
											<div className="text-center">
												<div className="w-12 h-12 mx-auto mb-3 bg-gray-200 rounded-full flex items-center justify-center">
													<svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
														<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
													</svg>
												</div>
												<h4 className="text-sm font-medium text-gray-700 mb-1">Anxiety Tracking</h4>
												<p className="text-xs text-gray-500">PSA score improvements</p>
											</div>
										</div>
									</div>
								</div>
							</div>
						)}
					</div>

					{/* Speeches Overview */}
					<div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
						<div className="flex justify-between items-center mb-4">
							<h2 className="text-2xl font-bold text-gray-900">Your Speeches</h2>
							<Link 
								href="/speeches"
								className="text-blue-600 hover:text-blue-800 text-sm font-medium"
							>
								View All →
							</Link>
						</div>
						
						{speeches.length === 0 ? (
							<div className="text-center py-8">
								<p className="text-gray-500 mb-4">No speeches created yet</p>
								<Link 
									href="/speeches/new"
									className="inline-flex items-center bg-blue-600 text-white px-4 py-2 rounded-md font-medium hover:bg-blue-700"
								>
									Create Your First Speech
								</Link>
							</div>
						) : (
							<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
								{speeches.slice(0, 6).map(speech => {
									const speechSessions = sessions.filter(s => s.speech_id === speech.id);
									const sessionCount = speechSessions.length;
									const hasImprovement = sessionCount > 1;
									
									return (
										<div key={speech.id} className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow bg-white">
											{/* Speech Header */}
											<div className="mb-4">
												<h3 className="font-bold text-gray-900 mb-2 text-lg">{speech.title}</h3>
												<div className="flex items-center space-x-2 mb-2">
													<span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
														{speech.context}
													</span>
													{speech.sessionCount > 0 && (
														<span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
															{speech.sessionCount} session{speech.sessionCount !== 1 ? 's' : ''}
														</span>
													)}
												</div>
												<p className="text-sm text-gray-600 line-clamp-2">{speech.description}</p>
											</div>

											{/* Progress Trend Mini Chart */}
											{hasImprovement && (
												<div className="mb-3">
													<div className="flex items-center justify-between mb-1">
														<span className="text-xs text-gray-500">Progress Trend</span>
														<span className="text-xs text-blue-600">{sessionCount} sessions</span>
													</div>
													<MiniTrendChart speechId={speech.id} sessions={sessions} />
												</div>
											)}

											{/* CSSEF Scores Section */}
											{speech.sessionCount > 0 && speech.avgOverallScore && (
												<div className="mb-4 space-y-3">
													{/* Overall Score and Improvement */}
													<div className="flex items-center justify-between">
														<div className="flex items-center space-x-2">
															<span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold ${getScoreColor(speech.avgOverallScore)}`}>
																{speech.avgOverallScore}% Overall
															</span>
															{speech.improvement !== undefined && speech.improvement !== 0 && (
																<div className={`flex items-center space-x-1 ${getImprovementColor(speech.improvement)}`}>
																	{getImprovementIcon(speech.improvement)}
																	<span className="text-xs font-medium">
																		{speech.improvement > 0 ? '+' : ''}{speech.improvement}%
																	</span>
																</div>
															)}
														</div>
													</div>

													{/* CSSEF Competencies Grid */}
													<div className="grid grid-cols-2 gap-2 text-xs">
														{getCSSEFCompetencies().map(competency => {
															const score = speech.cssefScores?.[competency.key as keyof CSSEFScores];
															return score ? (
																<div key={competency.key} className="flex justify-between items-center py-1">
																	<span className="text-gray-600 truncate">{competency.shortLabel}</span>
																	<span className={`px-2 py-0.5 rounded text-xs font-medium ${getScoreColor(score)}`}>
																		{score}
																	</span>
																</div>
															) : null;
														})}
													</div>
												</div>
											)}

											{/* PSA Score (if available) */}
											{speech.prpsa_completed && speech.prpsa_score && (
												<div className="mb-4 p-3 bg-purple-50 rounded-lg">
													<div className="flex items-center justify-between">
														<span className="text-sm font-medium text-purple-800">PSA Score</span>
														<span className="text-sm font-bold text-purple-900">{speech.prpsa_score}</span>
													</div>
												</div>
											)}

											{/* No Sessions State */}
											{speech.sessionCount === 0 && (
												<div className="mb-4 p-3 bg-gray-50 rounded-lg text-center">
													<p className="text-sm text-gray-500 mb-2">No practice sessions yet</p>
													<p className="text-xs text-gray-400">Start practicing to see CSSEF scores</p>
												</div>
											)}

											{/* Action Buttons */}
											<div className="flex justify-between items-center pt-3 border-t border-gray-100">
												<Link 
													href={`/speeches/${speech.id}`}
													className="text-blue-600 hover:text-blue-800 text-sm font-medium transition-colors"
												>
													View Details
												</Link>
												<Link 
													href={`/speeches/${speech.id}/sessions/new`}
													className="bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-green-700 transition-colors"
												>
													Practice
												</Link>
											</div>
										</div>
									);
								})}
							</div>
						)}
					</div>

					{/* Recent Sessions */}
					<div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
						<h2 className="text-2xl font-bold text-gray-900 mb-4">Recent Practice Sessions</h2>
						
						{sessions.length === 0 ? (
							<div className="text-center py-8">
								<p className="text-gray-500 mb-4">No practice sessions yet</p>
								<p className="text-sm text-gray-400">Start practicing to see your progress here</p>
							</div>
						) : (
							<div className="overflow-x-auto">
								<table className="w-full text-sm">
									<thead>
										<tr className="border-b border-gray-200">
											<th className="text-left py-3 px-3 font-medium text-gray-700">Speech</th>
											<th className="text-left py-3 px-3 font-medium text-gray-700">Date</th>
											<th className="text-center py-3 px-3 font-medium text-gray-700">Duration</th>
											<th className="text-center py-3 px-3 font-medium text-gray-700">Overall Score</th>
											<th className="text-center py-3 px-3 font-medium text-gray-700">Top CSSEF</th>
											<th className="text-center py-3 px-3 font-medium text-gray-700">Filler Rate</th>
											<th className="text-center py-3 px-3 font-medium text-gray-700">Actions</th>
										</tr>
									</thead>
									<tbody>
										{sessions.slice(0, 10).map(session => {
											// Find highest CSSEF score for this session
											const competencies = getCSSEFCompetencies();
											const cssefScores = competencies
												.map(comp => ({
													...comp,
													score: session.scores?.[comp.key as keyof CSSEFScores]
												}))
												.filter(comp => typeof comp.score === 'number')
												.sort((a, b) => (b.score as number) - (a.score as number));
											
											const topCSSEF = cssefScores[0];

											return (
												<tr key={session.id} className="border-b border-gray-100 hover:bg-gray-50">
													<td className="py-3 px-3">
														<div className="font-medium text-gray-900">{session.speechTitle}</div>
														<div className="text-xs text-gray-500">{session.speechContext}</div>
													</td>
													<td className="py-3 px-3 text-gray-600">
														{formatDate(session.created_at)}
													</td>
													<td className="py-3 px-3 text-center text-gray-600">
														{formatDuration(session.duration_seconds || 0)}
													</td>
													<td className="py-3 px-3 text-center">
														{session.scores?.overall_score ? (
															<span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold ${getScoreColor(session.scores.overall_score)}`}>
																{session.scores.overall_score}%
															</span>
														) : (
															<span className="text-gray-400 text-xs">N/A</span>
														)}
													</td>
													<td className="py-3 px-3 text-center">
														{topCSSEF ? (
															<div className="text-center">
																<div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold ${getScoreColor(topCSSEF.score as number)}`}>
																	{topCSSEF.score}%
																</div>
																<div className="text-xs text-gray-500 mt-1">
																	{topCSSEF.shortLabel}
																</div>
															</div>
														) : (
															<span className="text-gray-400 text-xs">N/A</span>
														)}
													</td>
													<td className="py-3 px-3 text-center">
														<span className={`font-medium ${
															(session.filler_word_percentage || 0) > 5 ? 'text-red-600' : 
															(session.filler_word_percentage || 0) > 2 ? 'text-orange-600' : 'text-green-600'
														}`}>
															{(session.filler_word_percentage || 0).toFixed(1)}%
														</span>
													</td>
													<td className="py-3 px-3 text-center">
														<Link 
															href={`/speeches/${session.speech_id}/sessions/${session.id}`}
															className="text-blue-600 hover:text-blue-800 text-sm font-medium"
														>
															View
														</Link>
													</td>
												</tr>
											);
										})}
									</tbody>
								</table>
							</div>
						)}
					</div>

					{/* Improvement Insights */}
					{sessions.length > 0 && (
						<div className="bg-white border border-gray-200 rounded-lg p-6">
							<h2 className="text-2xl font-bold text-gray-900 mb-4">Improvement Insights</h2>
							
							<div className="grid grid-cols-1 md:grid-cols-2 gap-6">
								{/* Progress Summary */}
								<div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4">
									<h3 className="text-lg font-semibold text-blue-900 mb-3">Progress Summary</h3>
									{speeches.filter(s => s.improvement && s.improvement > 0).length > 0 ? (
										<div className="space-y-2">
											<p className="text-sm text-blue-800">
												<span className="font-medium">
													{speeches.filter(s => s.improvement && s.improvement > 0).length}
												</span> speeches showing improvement
											</p>
											<p className="text-sm text-blue-800">
												Average improvement: <span className="font-medium text-green-600">
													+{Math.round((speeches.reduce((sum, s) => sum + (s.improvement || 0), 0) / speeches.length) * 10) / 10}%
												</span>
											</p>
											<p className="text-xs text-blue-600 mt-2">
												Regular practice sessions are helping build your speaking confidence and competency.
											</p>
										</div>
									) : (
										<p className="text-sm text-blue-800">
											Continue practicing to track your improvement over time.
										</p>
									)}
								</div>

								{/* Recommendations */}
								<div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg p-4">
									<h3 className="text-lg font-semibold text-green-900 mb-3">Recommendations</h3>
									<div className="space-y-2">
										{sessions.length < 5 && (
											<p className="text-sm text-green-800">
												📈 Practice more regularly to improve your scores
											</p>
										)}
										{stats.avgFillerWordsRate > 3 && (
											<p className="text-sm text-green-800">
												🎯 Focus on reducing filler words (currently {stats.avgFillerWordsRate}%)
											</p>
										)}
										{speeches.some(s => !s.prpsa_completed) && (
											<p className="text-sm text-green-800">
												📊 Complete PRPSA assessments to track anxiety reduction
											</p>
										)}
										{stats.avgCSSEFScore > 0 && stats.avgCSSEFScore < 70 && (
											<p className="text-sm text-green-800">
												💪 Keep practicing to improve your CSSEF competency scores
											</p>
										)}
									</div>
								</div>
							</div>
						</div>
					)}
				</div>

				<Toaster
					position="top-center"
					reverseOrder={false}
					toastOptions={{ duration: 2000 }}
				/>
			</main>
		</div>
	);
}

export default function Dashboard() {
	return (
		<Suspense fallback={
			<div className="flex justify-center items-center min-h-screen">
				<div className="text-lg">Loading dashboard...</div>
			</div>
		}>
			<DashboardContent />
		</Suspense>
	);
}
