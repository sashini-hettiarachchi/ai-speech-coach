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

// Force dynamic rendering
export const dynamic = 'force-dynamic';

const FillerWordsChart = dynamicImport(() => import("../../components/FillerWordsCharts"), { ssr: false });
const DeliveryMetricsTable = dynamicImport(() => import("../../components/DeliveryMetrics"), { ssr: false });
const PerformanceTrends = dynamicImport(() => import("../../components/PerformanceTrends"), { ssr: false });

function DashboardContent() {
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
					const speechSessionsResponse = await sessionApi.getSessions(speech.id);
					const speechSessions = speechSessionsResponse.sessions || speechSessionsResponse;
					
					// Get detailed session data for each session
					const detailedSessions = await Promise.all(
						speechSessions.map(async (session: any) => {
							try {
								const fullSession = await sessionApi.getSession(session.id);
								return {
									...fullSession,
									speechTitle: speech.title,
									speechContext: speech.context,
									speech_id: speech.id
								};
							} catch (error) {
								console.error(`Error loading session ${session.id}:`, error);
								// Fallback to basic session data
								return {
									...session,
									speechTitle: speech.title,
									speechContext: speech.context,
									speech_id: speech.id
								};
							}
						})
					);
					
					allSessions = [...allSessions, ...detailedSessions];

					// Calculate stats
					detailedSessions.forEach((session: any) => {
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
					{/* Welcome Header */}
					<div className="text-center mb-12">
						<h1 className="text-4xl font-bold text-slate-900 mb-2">
							Speech Coach Dashboard
						</h1>
						<p className="text-gray-600 mb-2">
							Track your speaking progress and improve your communication skills
						</p>
						{currentUser && (
							<p className="text-sm text-gray-500">
								Welcome back, {currentUser.name || currentUser.email || 'Speaker'}! 
							</p>
						)}
					</div>

					{/* Quick Actions */}
					<div className="flex justify-center space-x-4 mb-8">
						<Link 
							href="/speeches/new"
							className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors inline-flex items-center"
						>
							<svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
							</svg>
							New Speech
						</Link>
						<Link 
							href="/speeches"
							className="bg-gray-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-gray-700 transition-colors inline-flex items-center"
						>
							<svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
							</svg>
							Quick Practice
						</Link>
					</div>

					{/* Enhanced Quick Stats */}
					<div className="bg-white border border-gray-200 rounded-lg p-6 mb-8">
						<h2 className="text-xl font-bold text-gray-900 mb-4">Performance Overview</h2>
						
						{/* Quick Stats Grid */}
						<div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
							<div className="bg-blue-50 rounded-lg p-4">
								<h3 className="text-sm font-medium text-blue-800 mb-1">Total Speeches</h3>
								<p className="text-2xl font-bold text-blue-900">{stats.totalSpeeches}</p>
								<p className="text-xs text-blue-600 mt-1">
									{speeches.filter(s => s.completed).length} completed
								</p>
							</div>
							<div className="bg-green-50 rounded-lg p-4">
								<h3 className="text-sm font-medium text-green-800 mb-1">Total Sessions</h3>
								<p className="text-2xl font-bold text-green-900">{stats.totalSessions}</p>
								<p className="text-xs text-green-600 mt-1">
									{stats.totalPracticeTime}m practice time
								</p>
							</div>
							<div className="bg-purple-50 rounded-lg p-4">
								<h3 className="text-sm font-medium text-purple-800 mb-1">Avg Speaking Rate</h3>
								<p className="text-2xl font-bold text-purple-900">
									{sessions.length > 0 ? Math.round(
										sessions.reduce((sum, s) => sum + (s.words_per_minute || 0), 0) / sessions.length
									) : 0}
								</p>
								<p className="text-xs text-purple-600 mt-1">words per minute</p>
							</div>
							<div className="bg-orange-50 rounded-lg p-4">
								<h3 className="text-sm font-medium text-orange-800 mb-1">Avg Filler Rate</h3>
								<p className="text-2xl font-bold text-orange-900">{stats.avgFillerWordsRate}%</p>
								<p className="text-xs text-orange-600 mt-1">
									{stats.avgFillerWordsRate <= 2 ? 'Excellent' : 
									 stats.avgFillerWordsRate <= 5 ? 'Good' : 'Needs work'}
								</p>
							</div>
						</div>

						{/* Progress Indicators */}
						{sessions.length > 1 && (
							<div className="border-t border-gray-200 pt-4">
								<h4 className="text-sm font-semibold text-gray-700 mb-3">Recent Trends</h4>
								<div className="grid grid-cols-1 md:grid-cols-3 gap-4">
									{/* Filler Words Trend */}
									<div className="bg-gray-50 rounded-lg p-3">
										<div className="flex items-center justify-between">
											<span className="text-sm text-gray-600">Filler Words</span>
											{(() => {
												const recentSessions = sessions.slice(-3);
												const firstRate = recentSessions[0]?.filler_word_percentage || 0;
												const lastRate = recentSessions[recentSessions.length - 1]?.filler_word_percentage || 0;
												const trend = lastRate - firstRate;
												return (
													<span className={`text-xs font-medium ${
														trend < -0.5 ? 'text-green-600' : trend > 0.5 ? 'text-red-600' : 'text-gray-600'
													}`}>
														{trend < -0.5 ? '📈 Improving' : trend > 0.5 ? '📉 Increasing' : '➡️ Stable'}
													</span>
												);
											})()}
										</div>
									</div>

									{/* Speaking Rate Trend */}
									<div className="bg-gray-50 rounded-lg p-3">
										<div className="flex items-center justify-between">
											<span className="text-sm text-gray-600">Speaking Rate</span>
											{(() => {
												const recentSessions = sessions.slice(-3);
												const firstWpm = recentSessions[0]?.words_per_minute || 0;
												const lastWpm = recentSessions[recentSessions.length - 1]?.words_per_minute || 0;
												const trend = lastWpm - firstWpm;
												return (
													<span className={`text-xs font-medium ${
														Math.abs(trend) < 10 ? 'text-gray-600' : 'text-blue-600'
													}`}>
														{Math.abs(trend) < 10 ? '➡️ Stable' : 
														 trend > 0 ? '📈 Faster' : '📉 Slower'}
													</span>
												);
											})()}
										</div>
									</div>

									{/* Overall Score Trend */}
									<div className="bg-gray-50 rounded-lg p-3">
										<div className="flex items-center justify-between">
											<span className="text-sm text-gray-600">Overall Scores</span>
											{(() => {
												const recentSessions = sessions.slice(-3).filter(s => s.overall_score);
												if (recentSessions.length < 2) return <span className="text-xs text-gray-500">N/A</span>;
												const firstScore = recentSessions[0]?.overall_score || 0;
												const lastScore = recentSessions[recentSessions.length - 1]?.overall_score || 0;
												const trend = lastScore - firstScore;
												return (
													<span className={`text-xs font-medium ${
														trend > 0.2 ? 'text-green-600' : trend < -0.2 ? 'text-red-600' : 'text-gray-600'
													}`}>
														{trend > 0.2 ? '📈 Improving' : trend < -0.2 ? '📉 Declining' : '➡️ Stable'}
													</span>
												);
											})()}
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
							<>
								{/* Context Performance Breakdown */}
								{sessions.length > 0 && (
									<div className="mb-6 p-4 bg-gradient-to-r from-gray-50 to-blue-50 rounded-lg border border-gray-200">
										<h3 className="text-sm font-semibold text-gray-700 mb-3">Performance by Context</h3>
										<div className="grid grid-cols-1 md:grid-cols-3 gap-4">
											{['Academic', 'Storytelling', 'Persuasive'].map(context => {
												const contextSessions = sessions.filter(s => s.speechContext === context);
												if (contextSessions.length === 0) return null;
												
												const avgScore = contextSessions.reduce((sum, s) => sum + (s.overall_score || 0), 0) / contextSessions.length;
												const avgFiller = contextSessions.reduce((sum, s) => sum + (s.filler_word_percentage || 0), 0) / contextSessions.length;
												
												return (
													<div key={context} className="bg-white rounded-lg p-3 text-center">
														<div className="text-sm font-medium text-gray-700 mb-1">{context}</div>
														<div className="text-xl font-bold text-blue-600 mb-1">
															{avgScore > 0 ? (avgScore / 5 * 100).toFixed(0) + '%' : 'N/A'}
														</div>
														<div className="text-xs text-gray-500">
															{contextSessions.length} session{contextSessions.length !== 1 ? 's' : ''} • {avgFiller.toFixed(1)}% filler
														</div>
													</div>
												);
											})}
										</div>
									</div>
								)}

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
							</>
						)}
					</div>

					{/* Recent Sessions */}
					<div className="bg-white border border-gray-200 rounded-lg p-6 mb-8">
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

					{/* Performance Analytics */}
					{sessions.length > 0 && (
						<div className="mb-8">
							<PerformanceTrends 
								sessions={sessions} 
								speech={{
									id: 'dashboard',
									title: 'Overall Performance',
									description: 'Aggregated performance across all speeches',
									context: 'Mixed',
									goal: 'Continuous improvement',
									prpsa_completed: speeches.some(s => s.prpsa_completed),
									prpsa_score: speeches.find(s => s.prpsa_score)?.prpsa_score
								}} 
							/>
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
