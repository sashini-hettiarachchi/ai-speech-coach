"use client";

import { useEffect, useRef } from 'react';
import {
	Chart as ChartJS,
	CategoryScale,
	LinearScale,
	BarElement,
	Title,
	Tooltip,
	Legend,
	ChartOptions
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(
	CategoryScale,
	LinearScale,
	BarElement,
	Title,
	Tooltip,
	Legend
);

interface UserPRPSAData {
	user_id: number;
	participant_id: string;
	auth0_user_id: string;
	initial_prpsa: {
		score: number | null;
		anxiety_level: string | null;
	};
	post_prpsa: {
		score: number | null;
		anxiety_level: string | null;
	};
}

interface UserPRPSAComparisonProps {
	users: UserPRPSAData[];
}

export default function UserPRPSAComparison({ users }: UserPRPSAComparisonProps) {
	// Filter users who have at least one PRPSA assessment
	const usersWithData = users.filter(
		u => u.initial_prpsa.score !== null || u.post_prpsa.score !== null
	);

	if (usersWithData.length === 0) {
		return (
			<div className="text-center py-8 text-gray-500">
				No PRPSA assessment data available yet
			</div>
		);
	}

	// Prepare chart data - sort by participant_id to ensure consistent ordering
	const sortedUsers = [...usersWithData].sort((a, b) => {
		if (!a.participant_id) return 1;
		if (!b.participant_id) return -1;
		return a.participant_id.localeCompare(b.participant_id);
	});
	
	const labels = sortedUsers.map(u => u.participant_id || `User #${u.user_id}`);
	const initialScores = sortedUsers.map(u => u.initial_prpsa.score || 0);
	const postScores = sortedUsers.map(u => u.post_prpsa.score || 0);

	const data = {
		labels,
		datasets: [
			{
				label: 'Initial PRPSA',
				data: initialScores,
				backgroundColor: 'rgba(239, 68, 68, 0.7)', // Red for higher anxiety
				borderColor: 'rgba(239, 68, 68, 1)',
				borderWidth: 1,
			},
			{
				label: 'Post-Experimental PRPSA',
				data: postScores,
				backgroundColor: 'rgba(34, 197, 94, 0.7)', // Green for lower anxiety
				borderColor: 'rgba(34, 197, 94, 1)',
				borderWidth: 1,
			},
		],
	};

	const options: ChartOptions<'bar'> = {
		responsive: true,
		maintainAspectRatio: false,
		plugins: {
			legend: {
				position: 'top' as const,
			},
			title: {
				display: false,
			},
			tooltip: {
				callbacks: {
					afterLabel: (context) => {
						const userIndex = context.dataIndex;
						const user = sortedUsers[userIndex];
						const isInitial = context.datasetIndex === 0;
						const level = isInitial 
							? user.initial_prpsa.anxiety_level 
							: user.post_prpsa.anxiety_level;
						return level ? `Anxiety Level: ${level}` : '';
					},
				},
			},
		},
		scales: {
			y: {
				beginAtZero: true,
				max: 170,
				title: {
					display: true,
					text: 'PRPSA Score (34-170)',
				},
				ticks: {
					stepSize: 20,
				},
				// Add reference lines for anxiety levels
				grid: {
					color: (context) => {
						// High anxiety threshold at 131
						if (context.tick.value === 131) return 'rgba(239, 68, 68, 0.3)';
						// Moderate anxiety threshold at 98
						if (context.tick.value === 98) return 'rgba(251, 146, 60, 0.3)';
						return 'rgba(0, 0, 0, 0.1)';
					},
				},
			},
			x: {
				title: {
					display: true,
					text: 'Users',
				},
			},
		},
	};

	return (
		<div>
			<div className="h-96">
				<Bar data={data} options={options} />
			</div>
			
			{/* Legend for anxiety levels */}
			<div className="mt-6 p-4 bg-gray-50 rounded-lg">
				<h4 className="font-semibold text-sm text-gray-700 mb-2">PRPSA Anxiety Levels:</h4>
				<div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-xs">
					<div className="flex items-center space-x-2">
						<div className="w-4 h-4 bg-green-500 rounded"></div>
						<span className="text-gray-600">Low: &lt; 98</span>
					</div>
					<div className="flex items-center space-x-2">
						<div className="w-4 h-4 bg-orange-500 rounded"></div>
						<span className="text-gray-600">Moderate: 98-131</span>
					</div>
					<div className="flex items-center space-x-2">
						<div className="w-4 h-4 bg-red-500 rounded"></div>
						<span className="text-gray-600">High: &gt; 131</span>
					</div>
				</div>
			</div>

			{/* Summary Statistics */}
			<div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
				{sortedUsers.filter(u => u.initial_prpsa.score !== null && u.post_prpsa.score !== null).length > 0 && (
					<>
						<div className="p-3 bg-blue-50 rounded">
							<div className="text-xs text-blue-800 font-medium mb-1">Average Improvement</div>
							<div className="text-2xl font-bold text-blue-900">
								{(() => {
									const improvements = sortedUsers
										.filter(u => u.initial_prpsa.score !== null && u.post_prpsa.score !== null)
										.map(u => u.initial_prpsa.score! - u.post_prpsa.score!);
									const avg = improvements.reduce((a, b) => a + b, 0) / improvements.length;
									return `${avg > 0 ? '+' : ''}${avg.toFixed(1)}`;
								})()}
							</div>
							<div className="text-xs text-blue-600 mt-1">Points reduced</div>
						</div>
						<div className="p-3 bg-green-50 rounded">
							<div className="text-xs text-green-800 font-medium mb-1">Users Improved</div>
							<div className="text-2xl font-bold text-green-900">
								{sortedUsers.filter(u => 
									u.initial_prpsa.score !== null && 
									u.post_prpsa.score !== null && 
									u.initial_prpsa.score > u.post_prpsa.score
								).length}
							</div>
							<div className="text-xs text-green-600 mt-1">
								of {sortedUsers.filter(u => u.initial_prpsa.score !== null && u.post_prpsa.score !== null).length} total
							</div>
						</div>
						<div className="p-3 bg-purple-50 rounded">
							<div className="text-xs text-purple-800 font-medium mb-1">Completion Rate</div>
							<div className="text-2xl font-bold text-purple-900">
								{((sortedUsers.filter(u => u.initial_prpsa.score !== null && u.post_prpsa.score !== null).length / users.length) * 100).toFixed(0)}%
							</div>
							<div className="text-xs text-purple-600 mt-1">Both assessments completed</div>
						</div>
					</>
				)}
			</div>
		</div>
	);
}
