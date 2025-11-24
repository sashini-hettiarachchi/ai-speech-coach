"use client";

import { useState, useEffect } from "react";
import { useUser } from "@auth0/nextjs-auth0/client";
import { useRouter } from "next/navigation";
import { Toaster, toast } from "react-hot-toast";
import { adminApi } from "../../lib/api";
import Link from "next/link";
import dynamic from "next/dynamic";

// Dynamically import chart components
const UserPRPSAComparison = dynamic(() => import("../../components/UserPRPSAComparison"), { ssr: false });
const CSSEFImprovementChart = dynamic(() => import("../../components/CSSEFImprovementChart"), { ssr: false });

interface UserData {
	user_id: number;
	participant_id: string;
	auth0_user_id: string;
	created_at: string;
	speech_count: number;
	session_count: number;
	initial_prpsa: {
		score: number | null;
		anxiety_level: string | null;
		completed_at: string | null;
	};
	post_prpsa: {
		score: number | null;
		anxiety_level: string | null;
		completed_at: string | null;
	};
}

interface SessionData {
	session_id: number;
	session_number: number;
	created_at: string;
	user_id: number;
	participant_id: string;
	auth0_user_id: string;
	speech_id: number;
	speech_title: string;
	speech_context: string;
	overall_score: number | null;
	cssef_scores: {
		c1_topic_choice: number | null;
		c2_purpose: number | null;
		c3_supporting: number | null;
		c4_organization: number | null;
		c5_language: number | null;
		c6_vocal_variety: number | null;
		c7_pronunciation: number | null;
	};
	words_per_minute: number | null;
	filler_word_count: number | null;
	filler_word_percentage: number | null;
	duration_seconds: number | null;
}

export default function AdminDashboard() {
	const { user, isLoading } = useUser();
	const router = useRouter();
	const [loading, setLoading] = useState(true);
	const [users, setUsers] = useState<UserData[]>([]);
	const [allSessions, setAllSessions] = useState<SessionData[]>([]);
	const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
	const [selectedSpeechId, setSelectedSpeechId] = useState<number | null>(null);
	const [userSessions, setUserSessions] = useState<any[]>([]);
	const [activeTab, setActiveTab] = useState<'overview' | 'users' | 'sessions'>('overview');

	// Helper function to extract score from either a number or an object
	const getScoreValue = (score: any): number | null => {
		if (score === null || score === undefined) return null;
		if (typeof score === 'number') return score;
		if (typeof score === 'object' && score.score !== undefined) return score.score;
		return null;
	};

	// Helper function to format score for display
	const formatScore = (score: any): string => {
		const value = getScoreValue(score);
		return value !== null ? value.toFixed(1) : '-';
	};

	useEffect(() => {
		loadAdminData();
	}, []);

	useEffect(() => {
		if (selectedUserId) {
			loadUserSessions(selectedUserId);
			// Reset speech selection when user changes
			setSelectedSpeechId(null);
		}
	}, [selectedUserId]);

	const loadAdminData = async () => {
		try {
			setLoading(true);
			
			// Load all users with PRPSA scores
			const usersResponse = await adminApi.getAllUsers();
			setUsers(usersResponse.users || []);

			// Load all sessions
			const sessionsResponse = await adminApi.getAllSessions();
			setAllSessions(sessionsResponse.sessions || []);

		} catch (error) {
			console.error("Error loading admin data:", error);
			toast.error("Failed to load admin data");
		} finally {
			setLoading(false);
		}
	};

	const loadUserSessions = async (userId: number) => {
		try {
			const response = await adminApi.getUserSessions(userId);
			setUserSessions(response.sessions || []);
		} catch (error) {
			console.error("Error loading user sessions:", error);
			toast.error("Failed to load user sessions");
		}
	};

	const handleUserSelect = (userId: number) => {
		setSelectedUserId(userId === selectedUserId ? null : userId);
	};

	if (isLoading || loading) {
		return (
			<div className="flex justify-center items-center min-h-screen">
				<div className="text-lg">Loading admin dashboard...</div>
			</div>
		);
	}

	// Calculate statistics
	const totalUsers = users.length;
	const totalSessions = allSessions.length;
	const usersWithInitialPRPSA = users.filter(u => u.initial_prpsa.score !== null).length;
	const usersWithPostPRPSA = users.filter(u => u.post_prpsa.score !== null).length;
	const avgImprovement = users
		.filter(u => u.initial_prpsa.score !== null && u.post_prpsa.score !== null)
		.reduce((sum, u) => {
			const improvement = (u.initial_prpsa.score! - u.post_prpsa.score!);
			return sum + improvement;
		}, 0) / Math.max(1, users.filter(u => u.initial_prpsa.score !== null && u.post_prpsa.score !== null).length);

	return (
		<div className="flex max-w-7xl mx-auto flex-col py-2 min-h-screen">
			<main className="flex flex-1 w-full flex-col px-4">
				<div className="max-w-7xl mx-auto w-full">
					{/* Header */}
					<div className="text-center mb-8 mt-8">
						<h1 className="text-4xl font-bold text-slate-900 mb-2">
							Admin Dashboard
						</h1>
						<p className="text-gray-600">
							Monitor user progress and PRPSA improvements across all participants
						</p>
					</div>

					{/* Navigation Tabs */}
					<div className="flex justify-center space-x-4 mb-8 border-b border-gray-200">
						<button
							onClick={() => setActiveTab('overview')}
							className={`px-6 py-3 font-medium transition-colors ${
								activeTab === 'overview'
									? 'border-b-2 border-blue-600 text-blue-600'
									: 'text-gray-600 hover:text-gray-900'
							}`}
						>
							Overview
						</button>
						<button
							onClick={() => setActiveTab('users')}
							className={`px-6 py-3 font-medium transition-colors ${
								activeTab === 'users'
									? 'border-b-2 border-blue-600 text-blue-600'
									: 'text-gray-600 hover:text-gray-900'
							}`}
						>
							PRPSA Analysis
						</button>
						<button
							onClick={() => setActiveTab('sessions')}
							className={`px-6 py-3 font-medium transition-colors ${
								activeTab === 'sessions'
									? 'border-b-2 border-blue-600 text-blue-600'
									: 'text-gray-600 hover:text-gray-900'
							}`}
						>
							CSSEF Progress
						</button>
					</div>

					{/* Overview Tab */}
					{activeTab === 'overview' && (
						<div>
							{/* Statistics Cards */}
							<div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
								<div className="bg-blue-50 rounded-lg p-6">
									<h3 className="text-sm font-medium text-blue-800 mb-1">Total Users</h3>
									<p className="text-3xl font-bold text-blue-900">{totalUsers}</p>
								</div>
								<div className="bg-green-50 rounded-lg p-6">
									<h3 className="text-sm font-medium text-green-800 mb-1">Total Sessions</h3>
									<p className="text-3xl font-bold text-green-900">{totalSessions}</p>
								</div>
								<div className="bg-purple-50 rounded-lg p-6">
									<h3 className="text-sm font-medium text-purple-800 mb-1">PRPSA Completed</h3>
									<p className="text-3xl font-bold text-purple-900">
										{usersWithInitialPRPSA} / {usersWithPostPRPSA}
									</p>
									<p className="text-xs text-purple-600 mt-1">Initial / Post</p>
								</div>
								<div className="bg-orange-50 rounded-lg p-6">
									<h3 className="text-sm font-medium text-orange-800 mb-1">Avg PRPSA Reduction</h3>
									<p className="text-3xl font-bold text-orange-900">
										{avgImprovement > 0 ? '+' : ''}{avgImprovement.toFixed(1)}
									</p>
									<p className="text-xs text-orange-600 mt-1">
										{avgImprovement > 0 ? 'Decreased anxiety' : 'Increased anxiety'}
									</p>
								</div>
							</div>

							{/* Recent Activity */}
							<div className="bg-white border border-gray-200 rounded-lg p-6 mb-8">
								<h2 className="text-2xl font-bold text-gray-900 mb-4">Recent Activity</h2>
								<div className="overflow-x-auto">
									<table className="w-full text-sm">
										<thead>
											<tr className="border-b border-gray-200">
												<th className="text-left py-3 px-3 font-medium text-gray-700">User</th>
												<th className="text-left py-3 px-3 font-medium text-gray-700">Speech</th>
												<th className="text-center py-3 px-3 font-medium text-gray-700">Context</th>
												<th className="text-center py-3 px-3 font-medium text-gray-700">Overall Score</th>
												<th className="text-left py-3 px-3 font-medium text-gray-700">Date</th>
											</tr>
										</thead>
										<tbody>
											{allSessions.slice(0, 10).map((session) => (
												<tr key={session.session_id} className="border-b border-gray-100 hover:bg-gray-50">
													<td className="py-3 px-3">
														<div className="text-xs text-gray-500">
															{session.participant_id || `User #${session.user_id}`}
														</div>
													</td>
													<td className="py-3 px-3 text-gray-900">{session.speech_title}</td>
													<td className="py-3 px-3 text-center">
														<span className={`px-2 py-1 rounded text-xs font-medium ${
															session.speech_context === 'Academic' ? 'bg-blue-100 text-blue-800' :
															session.speech_context === 'Storytelling' ? 'bg-purple-100 text-purple-800' :
															'bg-green-100 text-green-800'
														}`}>
															{session.speech_context}
														</span>
													</td>
													<td className="py-3 px-3 text-center">
														<span className="font-semibold">
															{session.overall_score ? (session.overall_score / 5 * 100).toFixed(0) + '%' : 'N/A'}
														</span>
													</td>
													<td className="py-3 px-3 text-gray-600 text-xs">
														{new Date(session.created_at).toLocaleDateString()}
													</td>
												</tr>
											))}
										</tbody>
									</table>
								</div>
							</div>
						</div>
					)}

					{/* PRPSA Analysis Tab */}
					{activeTab === 'users' && (
						<div>
							{/* PRPSA Comparison Chart */}
							<div className="bg-white border border-gray-200 rounded-lg p-6 mb-8">
								<h2 className="text-2xl font-bold text-gray-900 mb-4">
									PRPSA Score Comparison (Pre vs Post)
								</h2>
								<p className="text-sm text-gray-600 mb-6">
									Lower scores indicate reduced public speaking anxiety. Positive improvements show decreased anxiety levels.
								</p>
								<UserPRPSAComparison users={users} />
							</div>

							{/* User Details Table */}
							<div className="bg-white border border-gray-200 rounded-lg p-6">
								<h2 className="text-2xl font-bold text-gray-900 mb-4">User PRPSA Details</h2>
								<div className="overflow-x-auto">
									<table className="w-full text-sm">
										<thead>
											<tr className="border-b border-gray-200">
												<th className="text-left py-3 px-3 font-medium text-gray-700">User ID</th>
												<th className="text-center py-3 px-3 font-medium text-gray-700">Speeches</th>
												<th className="text-center py-3 px-3 font-medium text-gray-700">Sessions</th>
												<th className="text-center py-3 px-3 font-medium text-gray-700">Initial PRPSA</th>
												<th className="text-center py-3 px-3 font-medium text-gray-700">Post PRPSA</th>
												<th className="text-center py-3 px-3 font-medium text-gray-700">Improvement</th>
											</tr>
										</thead>
										<tbody>
											{users.map((user) => {
												const improvement = user.initial_prpsa.score !== null && user.post_prpsa.score !== null
													? user.initial_prpsa.score - user.post_prpsa.score
													: null;
												
												return (
													<tr key={user.user_id} className="border-b border-gray-100 hover:bg-gray-50">
														<td className="py-3 px-3">
															<div className="font-medium">{user.participant_id || `User #${user.user_id}`}</div>
															<div className="text-xs text-gray-500">{user.auth0_user_id.substring(0, 20)}...</div>
														</td>
														<td className="py-3 px-3 text-center">{user.speech_count}</td>
														<td className="py-3 px-3 text-center">{user.session_count}</td>
														<td className="py-3 px-3 text-center">
															{user.initial_prpsa.score !== null ? (
																<div>
																	<div className="font-semibold">{user.initial_prpsa.score}</div>
																	<div className={`text-xs ${
																		user.initial_prpsa.anxiety_level === 'Low' ? 'text-green-600' :
																		user.initial_prpsa.anxiety_level === 'Moderate' ? 'text-orange-600' :
																		'text-red-600'
																	}`}>
																		{user.initial_prpsa.anxiety_level}
																	</div>
																</div>
															) : (
																<span className="text-gray-400">-</span>
															)}
														</td>
														<td className="py-3 px-3 text-center">
															{user.post_prpsa.score !== null ? (
																<div>
																	<div className="font-semibold">{user.post_prpsa.score}</div>
																	<div className={`text-xs ${
																		user.post_prpsa.anxiety_level === 'Low' ? 'text-green-600' :
																		user.post_prpsa.anxiety_level === 'Moderate' ? 'text-orange-600' :
																		'text-red-600'
																	}`}>
																		{user.post_prpsa.anxiety_level}
																	</div>
																</div>
															) : (
																<span className="text-gray-400">-</span>
															)}
														</td>
														<td className="py-3 px-3 text-center">
															{improvement !== null ? (
																<span className={`font-semibold ${
																	improvement > 0 ? 'text-green-600' : 
																	improvement < 0 ? 'text-red-600' : 
																	'text-gray-600'
																}`}>
																	{improvement > 0 ? '+' : ''}{improvement}
																</span>
															) : (
																<span className="text-gray-400">-</span>
															)}
														</td>
													</tr>
												);
											})}
										</tbody>
									</table>
								</div>
							</div>
						</div>
					)}

					{/* CSSEF Progress Tab */}
					{activeTab === 'sessions' && (
						<div>
							{/* Filters */}
							<div className="bg-white border border-gray-200 rounded-lg p-6 mb-8">
								<h2 className="text-xl font-bold text-gray-900 mb-4">Filter Data</h2>
								<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
									{/* User Filter */}
									<div>
										<label className="block text-sm font-medium text-gray-700 mb-2">
											Select User
										</label>
										<select
											value={selectedUserId || ''}
											onChange={(e) => setSelectedUserId(e.target.value ? parseInt(e.target.value) : null)}
											className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
										>
											<option value="">All Users</option>
											{users.filter(u => u.session_count > 0).map((user) => (
												<option key={user.user_id} value={user.user_id}>
													{user.participant_id || `User #${user.user_id}`} ({user.session_count} sessions)
												</option>
											))}
										</select>
									</div>

									{/* Speech Filter */}
									<div>
										<label className="block text-sm font-medium text-gray-700 mb-2">
											Select Speech {selectedUserId ? '' : '(Select user first)'}
										</label>
										<select
											value={selectedSpeechId || ''}
											onChange={(e) => setSelectedSpeechId(e.target.value ? parseInt(e.target.value) : null)}
											className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
											disabled={!selectedUserId}
										>
											<option value="">All Speeches</option>
											{selectedUserId && (() => {
												// Get unique speeches for selected user that have sessions
												const userSessionsData = userSessions;
												const uniqueSpeeches = Array.from(
													new Map(
														userSessionsData.map((s: any) => [s.speech_id, s])
													).values()
												);
												return uniqueSpeeches.map((session: any) => (
													<option key={session.speech_id} value={session.speech_id}>
														{session.speech_title} ({session.speech_context}) - {userSessionsData.filter((s: any) => s.speech_id === session.speech_id).length} sessions
													</option>
												));
											})()}
										</select>
									</div>
								</div>
							</div>

							{/* CSSEF Improvement Chart */}
							{selectedUserId && userSessions.length > 0 && (
								<div className="bg-white border border-gray-200 rounded-lg p-6 mb-8">
									<h2 className="text-2xl font-bold text-gray-900 mb-4">
										CSSEF Competency Progress - {users.find(u => u.user_id === selectedUserId)?.participant_id || `User #${selectedUserId}`}
										{selectedSpeechId && (() => {
											const speech = userSessions.find((s: any) => s.speech_id === selectedSpeechId);
											return speech ? ` - ${speech.speech_title}` : '';
										})()}
									</h2>
									<p className="text-sm text-gray-600 mb-6">
										Track improvement across all 7 CSSEF competencies over practice sessions
										{selectedSpeechId && ' for this specific speech'}
									</p>
									<CSSEFImprovementChart 
										sessions={selectedSpeechId 
											? userSessions.filter((s: any) => s.speech_id === selectedSpeechId)
											: userSessions
										} 
									/>
								</div>
							)}

							{/* Overall Score Statistics */}
							{(selectedUserId || allSessions.length > 0) && (
								<div className="bg-white border border-gray-200 rounded-lg p-6 mb-8">
									<h2 className="text-xl font-bold text-gray-900 mb-4">Overall Score Statistics</h2>
									<div className="grid grid-cols-1 md:grid-cols-4 gap-4">
										{(() => {
											// Get sessions based on filters
											let filteredSessions = selectedUserId ? userSessions : allSessions;
											if (selectedSpeechId) {
												filteredSessions = filteredSessions.filter((s: any) => s.speech_id === selectedSpeechId);
											}
											
											const sessionsWithScores = filteredSessions.filter((s: any) => s.overall_score);
											
											if (sessionsWithScores.length === 0) {
												return (
													<div className="col-span-4 text-center text-gray-500 py-4">
														No sessions with overall scores yet
													</div>
												);
											}
											
											const scores = sessionsWithScores.map((s: any) => s.overall_score);
											const avgScore = scores.reduce((a: number, b: number) => a + b, 0) / scores.length;
											const maxScore = Math.max(...scores);
											const minScore = Math.min(...scores);
											const latestScore = sessionsWithScores[sessionsWithScores.length - 1]?.overall_score || 0;
											const firstScore = sessionsWithScores[0]?.overall_score || 0;
											const improvement = latestScore - firstScore;
											
											return (
												<>
													<div className="bg-blue-50 rounded-lg p-4">
														<div className="text-sm text-blue-800 font-medium mb-1">Average Score</div>
														<div className="text-3xl font-bold text-blue-900">
															{(avgScore / 5 * 100).toFixed(0)}%
														</div>
														<div className="text-xs text-blue-600 mt-1">
															{avgScore.toFixed(2)}/5.0
														</div>
													</div>
													
													<div className="bg-green-50 rounded-lg p-4">
														<div className="text-sm text-green-800 font-medium mb-1">Highest Score</div>
														<div className="text-3xl font-bold text-green-900">
															{(maxScore / 5 * 100).toFixed(0)}%
														</div>
														<div className="text-xs text-green-600 mt-1">
															{maxScore.toFixed(2)}/5.0
														</div>
													</div>
													
													<div className="bg-orange-50 rounded-lg p-4">
														<div className="text-sm text-orange-800 font-medium mb-1">Lowest Score</div>
														<div className="text-3xl font-bold text-orange-900">
															{(minScore / 5 * 100).toFixed(0)}%
														</div>
														<div className="text-xs text-orange-600 mt-1">
															{minScore.toFixed(2)}/5.0
														</div>
													</div>
													
													<div className={`${
														improvement > 0 ? 'bg-emerald-50' : 
														improvement < 0 ? 'bg-red-50' : 
														'bg-gray-50'
													} rounded-lg p-4`}>
														<div className={`text-sm font-medium mb-1 ${
															improvement > 0 ? 'text-emerald-800' : 
															improvement < 0 ? 'text-red-800' : 
															'text-gray-800'
														}`}>
															Improvement
														</div>
														<div className={`text-3xl font-bold ${
															improvement > 0 ? 'text-emerald-900' : 
															improvement < 0 ? 'text-red-900' : 
															'text-gray-900'
														}`}>
															{improvement > 0 ? '+' : ''}{(improvement / 5 * 100).toFixed(0)}%
														</div>
														<div className={`text-xs mt-1 ${
															improvement > 0 ? 'text-emerald-600' : 
															improvement < 0 ? 'text-red-600' : 
															'text-gray-600'
														}`}>
															First to Latest
														</div>
													</div>
												</>
											);
										})()}
									</div>
								</div>
							)}

							{/* Sessions Table */}
							<div className="bg-white border border-gray-200 rounded-lg p-6">
								<h2 className="text-2xl font-bold text-gray-900 mb-4">
									{selectedUserId 
										? `Sessions for ${users.find(u => u.user_id === selectedUserId)?.participant_id || `User #${selectedUserId}`}` 
										: 'All Sessions'}
									{selectedSpeechId && (() => {
										const speech = userSessions.find((s: any) => s.speech_id === selectedSpeechId);
										return speech ? ` - ${speech.speech_title}` : '';
									})()}
								</h2>
								<div className="overflow-x-auto">
									<table className="w-full text-sm">
										<thead>
											<tr className="border-b border-gray-200">
												{/* <th className="text-left py-3 px-3 font-medium text-gray-700">User</th> */}
												<th className="text-left py-3 px-3 font-medium text-gray-700">Speech</th>
												<th className="text-center py-3 px-3 font-medium text-gray-700">Session #</th>
												<th className="text-center py-3 px-3 font-medium text-gray-700">Overall</th>
												<th className="text-center py-3 px-3 font-medium text-gray-700">Filler Words</th>
												<th className="text-center py-3 px-3 font-medium text-gray-700">C1</th>
												<th className="text-center py-3 px-3 font-medium text-gray-700">C2</th>
												<th className="text-center py-3 px-3 font-medium text-gray-700">C3</th>
												<th className="text-center py-3 px-3 font-medium text-gray-700">C4</th>
												<th className="text-center py-3 px-3 font-medium text-gray-700">C5</th>
												<th className="text-center py-3 px-3 font-medium text-gray-700">C6</th>
												<th className="text-center py-3 px-3 font-medium text-gray-700">C7</th>
												<th className="text-left py-3 px-3 font-medium text-gray-700">Date</th>
											</tr>
										</thead>
										<tbody>
											{(() => {
												// Get sessions based on filters
												let filteredSessions = selectedUserId ? userSessions : allSessions;
												
												// Apply speech filter if selected
												if (selectedSpeechId) {
													filteredSessions = filteredSessions.filter((s: any) => s.speech_id === selectedSpeechId);
												}
												
												return filteredSessions.map((session: any) => (
													<tr key={session.session_id} className="border-b border-gray-100 hover:bg-gray-50">
														{/* <td className="py-3 px-3">
															<div className="text-xs text-gray-500">
																{session.participant_id || `User #${session.user_id}`}
															</div>
														</td> */}
														<td className="py-3 px-3">
															<div className="font-medium text-gray-900">{session.speech_title}</div>
															<div className="text-xs text-gray-500">{session.speech_context}</div>
														</td>
														<td className="py-3 px-3 text-center">{session.session_number}</td>
														<td className="py-3 px-3 text-center">
															{session.overall_score ? (
																<div>
																	<div className={`font-bold text-base ${
																		(session.overall_score / 5 * 100) >= 80 ? 'text-green-600' :
																		(session.overall_score / 5 * 100) >= 60 ? 'text-blue-600' :
																		(session.overall_score / 5 * 100) >= 40 ? 'text-orange-600' :
																		'text-red-600'
																	}`}>
																		{(session.overall_score / 5 * 100).toFixed(0)}%
																	</div>
																	<div className="text-xs text-gray-500">
																		{session.overall_score.toFixed(2)}/5.0
																	</div>
																</div>
															) : (
																<span className="text-gray-400">-</span>
															)}
														</td>
														<td className="py-3 px-3 text-center">
															{session.filler_word_count !== null && session.filler_word_count !== undefined ? (
																<div>
																	<div className={`font-bold text-base ${
																		session.filler_word_count === 0 ? 'text-green-600' :
																		session.filler_word_count <= 5 ? 'text-blue-600' :
																		session.filler_word_count <= 10 ? 'text-orange-600' :
																		'text-red-600'
																	}`}>
																		{session.filler_word_count}
																	</div>
																	{session.filler_word_percentage !== null && (
																		<div className="text-xs text-gray-500">
																			{session.filler_word_percentage.toFixed(1)}%
																		</div>
																	)}
																</div>
															) : (
																<span className="text-gray-400">-</span>
															)}
														</td>
														<td className="py-3 px-3 text-center">
															{formatScore(session.cssef_scores?.c1_topic_choice)}
														</td>
														<td className="py-3 px-3 text-center">
															{formatScore(session.cssef_scores?.c2_purpose)}
														</td>
														<td className="py-3 px-3 text-center">
															{formatScore(session.cssef_scores?.c3_supporting)}
														</td>
														<td className="py-3 px-3 text-center">
															{formatScore(session.cssef_scores?.c4_organization)}
														</td>
														<td className="py-3 px-3 text-center">
															{formatScore(session.cssef_scores?.c5_language)}
														</td>
														<td className="py-3 px-3 text-center">
															{formatScore(session.cssef_scores?.c6_vocal_variety)}
														</td>
														<td className="py-3 px-3 text-center">
															{formatScore(session.cssef_scores?.c7_pronunciation)}
														</td>
														<td className="py-3 px-3 text-xs text-gray-600">
															{new Date(session.created_at).toLocaleDateString()}
														</td>
													</tr>
												));
											})()}
										</tbody>
									</table>
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
