"use client";

import Image from "next/image";
import { useRef, useState, useEffect } from "react";
import { useRouter, useSearchParams } from 'next/navigation';
import { Toaster, toast } from "react-hot-toast";
import LoadingDots from "../../components/LoadingDots";
import { sessionApi, speechApi } from "../../lib/api";
import ReactMarkdown from "react-markdown";
import dynamic from "next/dynamic";
import Link from "next/link";
import { useUser } from "@auth0/nextjs-auth0";
const FillerWordsChart = dynamic(() => import("../../components/FillerWordsCharts"), { ssr: false });
const DeliveryMetricsTable = dynamic(() => import("../../components/DeliveryMetrics"), { ssr: false });

export default function Dashboard() {
	const { user : currentUser, isLoading } = useUser();
	console.log("user", currentUser)
	const router = useRouter();
	const searchParams = useSearchParams();
	const [loading, setLoading] = useState(true);
	const [speeches, setSpeeches] = useState<any[]>([]);
	const [sessions, setSessions] = useState<any[]>([]);
	const [stats, setStats] = useState({
		totalSpeeches: 0,
		totalSessions: 0,
		totalPracticeTime: 0,
		avgFillerWordsRate: 0
	});


	useEffect(() => {
		loadDashboardData();
	}, []);

	const loadDashboardData = async () => {
		try {
			setLoading(true);
			// Load speeches
			const speechData = await speechApi.getSpeeches();
			const speechesList = speechData.speeches || [];
			setSpeeches(speechesList);

			// Load all sessions for all speeches
			let allSessions: any[] = [];
			let totalPracticeTime = 0;
			let totalFillerWords = 0;
			let sessionsWithFillerData = 0;

			for (const speech of speechesList) {
				try {
					const speechSessions = await sessionApi.getSessions(speech.id);
					const sessionsWithSpeechInfo = speechSessions.map((session: any) => ({
						...session,
						speechTitle: speech.title,
						speechContext: speech.context
					}));
					allSessions = [...allSessions, ...sessionsWithSpeechInfo];

					// Calculate stats
					sessionsWithSpeechInfo.forEach((session: any) => {
						totalPracticeTime += session.duration_seconds || 0;
						if (session.filler_word_percentage !== undefined) {
							totalFillerWords += session.filler_word_percentage;
							sessionsWithFillerData++;
						}
					});
				} catch (error) {
					console.error(`Error loading sessions for speech ${speech.id}:`, error);
				}
			}

			setSessions(allSessions);
			setStats({
				totalSpeeches: speechesList.length,
				totalSessions: allSessions.length,
				totalPracticeTime: Math.round(totalPracticeTime / 60), // Convert to minutes
				avgFillerWordsRate: sessionsWithFillerData > 0 ? 
					Math.round((totalFillerWords / sessionsWithFillerData) * 10) / 10 : 0
			});

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
			{currentUser && (
				<div className="w-full px-4 mt-12 sm:mt-20 mb-8">
					<div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
						<div className="flex items-center space-x-4">
							{currentUser.picture && (
								<img
									src={currentUser.picture}
									alt="Profile"
									className="w-16 h-16 rounded-full"
								/>
							)}
							<div>
								<h2 className="text-2xl font-bold text-gray-900">
									Welcome back, {currentUser.name || currentUser.email || 'User'}!
								</h2>
								<p className="text-gray-600">{currentUser.email}</p>
								{!currentUser && (
									<p className="text-sm text-orange-600 mt-1">
										Demo Mode - Auth0 not configured
									</p>
								)}
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
							className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
						>
							+ New Speech
						</Link>
						<Link 
							href="/speeches"
							className="bg-gray-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-gray-700 transition-colors"
						>
							Practice Session
						</Link>
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
							<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
								{speeches.slice(0, 6).map(speech => (
									<div key={speech.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
										<h3 className="font-semibold text-gray-900 mb-2">{speech.title}</h3>
										<p className="text-sm text-gray-600 mb-2">{speech.context}</p>
										<p className="text-xs text-gray-500 mb-3 line-clamp-2">{speech.description}</p>
										<div className="flex justify-between items-center">
											<Link 
												href={`/speeches/${speech.id}`}
												className="text-blue-600 hover:text-blue-800 text-sm font-medium"
											>
												View Details
											</Link>
											<Link 
												href={`/speeches/${speech.id}/sessions/new`}
												className="bg-green-600 text-white px-3 py-1 rounded text-xs font-medium hover:bg-green-700"
											>
												Practice
											</Link>
										</div>
									</div>
								))}
							</div>
						)}
					</div>

					{/* Recent Sessions */}
					<div className="bg-white border border-gray-200 rounded-lg p-6">
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
											<th className="text-center py-3 px-3 font-medium text-gray-700">WPM</th>
											<th className="text-center py-3 px-3 font-medium text-gray-700">Filler Rate</th>
											<th className="text-center py-3 px-3 font-medium text-gray-700">Actions</th>
										</tr>
									</thead>
									<tbody>
										{sessions.slice(0, 10).map(session => (
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
												<td className="py-3 px-3 text-center text-gray-600">
													{Math.round(session.words_per_minute || 0)}
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
										))}
									</tbody>
								</table>
							</div>
						)}
					</div>
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
