"use client";

import { useEffect } from 'react';
import {
	Chart as ChartJS,
	CategoryScale,
	LinearScale,
	PointElement,
	LineElement,
	Title,
	Tooltip,
	Legend,
	ChartOptions
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
	CategoryScale,
	LinearScale,
	PointElement,
	LineElement,
	Title,
	Tooltip,
	Legend
);

interface SessionData {
	session_id: number;
	session_number: number;
	created_at: string;
	overall_score?: number | null;
	cssef_scores: {
		c1_topic_choice: { score: number | null } | number | null;
		c2_purpose: { score: number | null } | number | null;
		c3_supporting: { score: number | null } | number | null;
		c4_organization: { score: number | null } | number | null;
		c5_language: { score: number | null } | number | null;
		c6_vocal_variety: { score: number | null } | number | null;
		c7_pronunciation: { score: number | null } | number | null;
	};
}

interface CSSEFImprovementChartProps {
	sessions: SessionData[];
}

export default function CSSEFImprovementChart({ sessions }: CSSEFImprovementChartProps) {
	if (sessions.length === 0) {
		return (
			<div className="text-center py-8 text-gray-500">
				No session data available
			</div>
		);
	}

	// Helper function to extract score value
	const getScore = (scoreData: { score: number | null } | number | null): number | null => {
		if (scoreData === null || scoreData === undefined) return null;
		if (typeof scoreData === 'number') return scoreData;
		if (typeof scoreData === 'object' && 'score' in scoreData) return scoreData.score;
		return null;
	};

	// Sort sessions by session number
	const sortedSessions = [...sessions].sort((a, b) => a.session_number - b.session_number);

	// Prepare chart data
	const labels = sortedSessions.map(s => `Session ${s.session_number}`);

	const competencies = [
		{ key: 'c1_topic_choice', label: 'C1: Topic Choice', color: 'rgb(255, 99, 132)' },
		{ key: 'c2_purpose', label: 'C2: Purpose', color: 'rgb(54, 162, 235)' },
		{ key: 'c3_supporting', label: 'C3: Supporting Material', color: 'rgb(255, 206, 86)' },
		{ key: 'c4_organization', label: 'C4: Organization', color: 'rgb(75, 192, 192)' },
		{ key: 'c5_language', label: 'C5: Language', color: 'rgb(153, 102, 255)' },
		{ key: 'c6_vocal_variety', label: 'C6: Vocal Variety', color: 'rgb(255, 159, 64)' },
		{ key: 'c7_pronunciation', label: 'C7: Pronunciation', color: 'rgb(201, 203, 207)' },
	];

	// Create datasets for CSSEF competencies
	const datasets = competencies.map(comp => ({
		label: comp.label,
		data: sortedSessions.map(s => getScore(s.cssef_scores[comp.key as keyof typeof s.cssef_scores])),
		borderColor: comp.color,
		backgroundColor: comp.color.replace('rgb', 'rgba').replace(')', ', 0.5)'),
		tension: 0.3,
		spanGaps: true,
	}));

	// Add Overall Score as a bold black line
	const overallScoreDataset = {
		label: 'Overall Score',
		data: sortedSessions.map(s => s.overall_score || null),
		borderColor: 'rgb(0, 0, 0)',
		backgroundColor: 'rgba(0, 0, 0, 0.5)',
		borderWidth: 3,
		tension: 0.3,
		spanGaps: true,
		borderDash: [5, 5], // Dashed line to distinguish from competency lines
	};

	// Add overall score dataset at the beginning for prominence
	const allDatasets = [overallScoreDataset, ...datasets];

	const data = {
		labels,
		datasets: allDatasets,
	};

	const options: ChartOptions<'line'> = {
		responsive: true,
		maintainAspectRatio: false,
		interaction: {
			mode: 'index' as const,
			intersect: false,
		},
		plugins: {
			legend: {
				position: 'top' as const,
			},
			title: {
				display: false,
			},
			tooltip: {
				callbacks: {
					label: (context) => {
						const label = context.dataset.label || '';
						const value = context.parsed.y;
						return value !== null ? `${label}: ${value.toFixed(1)}/5` : `${label}: N/A`;
					},
				},
			},
		},
		scales: {
			y: {
				beginAtZero: true,
				max: 5,
				title: {
					display: true,
					text: 'Score (0-5)',
				},
				ticks: {
					stepSize: 0.5,
				},
			},
			x: {
				title: {
					display: true,
					text: 'Practice Sessions',
				},
			},
		},
	};

	// Calculate average improvements
	const calculateImprovement = (key: string) => {
		const sessionsWithScores = sortedSessions.filter(s => {
			const score = getScore(s.cssef_scores[key as keyof typeof s.cssef_scores]);
			return score !== null;
		});

		if (sessionsWithScores.length < 2) return null;

		const firstSession = sessionsWithScores[0];
		const lastSession = sessionsWithScores[sessionsWithScores.length - 1];
		
		const firstScore = getScore(firstSession.cssef_scores[key as keyof typeof firstSession.cssef_scores]);
		const lastScore = getScore(lastSession.cssef_scores[key as keyof typeof lastSession.cssef_scores]);

		if (firstScore === null || lastScore === null) return null;

		return lastScore - firstScore;
	};

	return (
		<div>
			<div className="h-96">
				<Line data={data} options={options} />
			</div>

			{/* Improvement Summary */}
			<div className="mt-6 grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
				{competencies.map(comp => {
					const improvement = calculateImprovement(comp.key);
					return (
						<div key={comp.key} className="p-3 bg-gray-50 rounded-lg text-center">
							<div className="text-xs font-medium text-gray-700 mb-1">
								{comp.label.split(':')[0]}
							</div>
							{improvement !== null ? (
								<div>
									<div className={`text-xl font-bold ${
										improvement > 0.3 ? 'text-green-600' : 
										improvement < -0.3 ? 'text-red-600' : 
										'text-gray-600'
									}`}>
										{improvement > 0 ? '+' : ''}{improvement.toFixed(2)}
									</div>
									<div className="text-xs text-gray-500">
										{improvement > 0 ? '📈' : improvement < 0 ? '📉' : '➡️'}
									</div>
								</div>
							) : (
								<div className="text-sm text-gray-400">N/A</div>
							)}
						</div>
					);
				})}
			</div>

			{/* Overall Progress Summary */}
			<div className="mt-4 p-4 bg-blue-50 rounded-lg">
				<h4 className="font-semibold text-sm text-blue-900 mb-2">Overall Progress</h4>
				<div className="grid grid-cols-2 md:grid-cols-5 gap-3">
					<div>
						<div className="text-xs text-blue-700 mb-1">Total Sessions</div>
						<div className="text-2xl font-bold text-blue-900">{sortedSessions.length}</div>
					</div>
					
					{/* Initial Overall Score */}
					<div>
						<div className="text-xs text-blue-700 mb-1">Initial Overall Score</div>
						<div className="text-2xl font-bold text-blue-900">
							{(() => {
								const firstSession = sortedSessions[0];
								if (!firstSession?.overall_score) return 'N/A';
								const percentage = (firstSession.overall_score / 5 * 100).toFixed(0);
								return `${percentage}%`;
							})()}
						</div>
						<div className="text-xs text-blue-600">
							{(() => {
								const firstSession = sortedSessions[0];
								if (!firstSession?.overall_score) return '';
								return `${firstSession.overall_score.toFixed(2)}/5.0`;
							})()}
						</div>
					</div>
					
					{/* Latest Overall Score */}
					<div>
						<div className="text-xs text-blue-700 mb-1">Latest Overall Score</div>
						<div className="text-2xl font-bold text-blue-900">
							{(() => {
								const lastSession = sortedSessions[sortedSessions.length - 1];
								if (!lastSession?.overall_score) return 'N/A';
								const percentage = (lastSession.overall_score / 5 * 100).toFixed(0);
								return `${percentage}%`;
							})()}
						</div>
						<div className="text-xs text-blue-600">
							{(() => {
								const lastSession = sortedSessions[sortedSessions.length - 1];
								if (!lastSession?.overall_score) return '';
								return `${lastSession.overall_score.toFixed(2)}/5.0`;
							})()}
						</div>
					</div>
					
					{/* Overall Score Improvement */}
					<div>
						<div className="text-xs text-blue-700 mb-1">Overall Score Change</div>
						<div className={`text-2xl font-bold ${(() => {
							const firstSession = sortedSessions[0];
							const lastSession = sortedSessions[sortedSessions.length - 1];
							if (!firstSession?.overall_score || !lastSession?.overall_score) return 'text-gray-600';
							const change = lastSession.overall_score - firstSession.overall_score;
							return change > 0 ? 'text-green-600' : change < 0 ? 'text-red-600' : 'text-gray-600';
						})()}`}>
							{(() => {
								const firstSession = sortedSessions[0];
								const lastSession = sortedSessions[sortedSessions.length - 1];
								if (!firstSession?.overall_score || !lastSession?.overall_score) return 'N/A';
								const change = lastSession.overall_score - firstSession.overall_score;
								const percentage = (change / 5 * 100).toFixed(0);
								return `${change > 0 ? '+' : ''}${percentage}%`;
							})()}
						</div>
						<div className="text-xs text-blue-600">
							{(() => {
								const firstSession = sortedSessions[0];
								const lastSession = sortedSessions[sortedSessions.length - 1];
								if (!firstSession?.overall_score || !lastSession?.overall_score) return '';
								const change = lastSession.overall_score - firstSession.overall_score;
								return `${change > 0 ? '+' : ''}${change.toFixed(2)}`;
							})()}
						</div>
					</div>
					
					<div>
						<div className="text-xs text-blue-700 mb-1">Competencies Improved</div>
						<div className="text-2xl font-bold text-blue-900">
							{competencies.filter(c => {
								const imp = calculateImprovement(c.key);
								return imp !== null && imp > 0;
							}).length} / 7
						</div>
					</div>
				</div>
			</div>
		</div>
	);
}
