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
	const [loading, setLoading] = useState(false);
	const [fillerWords, setFillerWords] = useState<any>("");
	const [recommendations, setRecommendations] = useState("");
	const [transcript, setTranscript] = useState("");
	const [deliveryMetrics, setDeliveryMetrics] = useState<any>(null);
	const [audioFile, setAudioFile] = useState<File | null>(null);
	const [selectedSpeechId, setSelectedSpeechId] = useState<string>("");
	const [speeches, setSpeeches] = useState<any[]>([]);
	const [selectedSpeech, setSelectedSpeech] = useState<any>(null);
	const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;


	// useEffect(() => {
	// 	// Load speeches when component mounts (with or without real auth)
	// 	loadSpeeches();
	// 	// Check if speech ID is provided in URL
	// 	const speechIdFromUrl = searchParams.get('speechId');
	// 	if (speechIdFromUrl) {
	// 		setSelectedSpeechId(speechIdFromUrl);
	// 	}
	// }, [searchParams]);

	useEffect(() => {
		if (selectedSpeechId && speeches.length > 0) {
			const speech = speeches.find(s => s.id === selectedSpeechId);
			setSelectedSpeech(speech);
		}
	}, [selectedSpeechId, speeches]);

	const loadSpeeches = async () => {
		try {
			const data = await speechApi.getSpeeches();
			setSpeeches(data.speeches || []);
		} catch (error) {
			console.error("Error loading speeches:", error);
			toast.error("Failed to load speeches");
		}
	};

	if (isLoading) {
		return <div>Loading...</div>;
	}

	const handleAnalyseSpeech = async () => {
		if (!audioFile) {
			toast.error("Please upload an audio file.");
			return;
		}
		
		if (!selectedSpeechId) {
			toast.error("Please select a speech first.");
			return;
		}
		
		setLoading(true);
		try {
			const data = await sessionApi.analyzeAndCreateSession(selectedSpeechId, audioFile);
			setFillerWords(data.fillers);
			setRecommendations(data.recommendations);
			setTranscript(data.transcript);
			if (data.delivery_metrics) setDeliveryMetrics(data.delivery_metrics);
			toast.success("Speech analysis completed!");
		} catch (error) {
			toast.error("Error analyzing speech");
			console.error(error);
		} finally {
			setLoading(false);
		}
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
						<div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
							<div className="bg-blue-50 rounded-lg p-4">
								<h3 className="text-sm font-medium text-blue-800 mb-1">Total Speeches</h3>
								<p className="text-2xl font-bold text-blue-900">{speeches.length}</p>
							</div>
							<div className="bg-green-50 rounded-lg p-4">
								<h3 className="text-sm font-medium text-green-800 mb-1">Quick Actions</h3>
								<Link 
									href="/speeches/new"
									className="text-sm text-green-700 hover:text-green-900 font-medium"
								>
									+ Create New Speech
								</Link>
							</div>
							<div className="bg-purple-50 rounded-lg p-4">
								<h3 className="text-sm font-medium text-purple-800 mb-1">Recent Activity</h3>
								<p className="text-sm text-purple-700">
									{speeches.length > 0 ? 'Ready to practice!' : 'Start your journey'}
								</p>
							</div>
						</div>
					</div>
				</div>
			)}

			<main className="flex flex-1 w-full flex-col items-center justify-center text-center px-4">
				<h1 className="sm:text-6xl text-4xl max-w-[708px] font-bold text-slate-900">
					{selectedSpeech ? `Practice: ${selectedSpeech.title}` : 'Practice Session'}
				</h1>

				{selectedSpeech && (
					<div className="max-w-xl w-full mt-6 p-4 bg-blue-50 rounded-lg">
						<p className="text-sm text-blue-800 mb-2">
							<strong>Context:</strong> {selectedSpeech.context}
						</p>
						<p className="text-sm text-blue-700">
							<strong>Goal:</strong> {selectedSpeech.goal}
						</p>
					</div>
				)}

				<div className="max-w-xl w-full">
					{/* Speech Selection */}
					<div className="flex mt-10 items-center space-x-3">
						<Image
							src="/2-black.png"
							width={30}
							height={30}
							alt="speech icon"
							className="mb-5 sm:mb-0"
						/>
						<p className="text-left font-medium">
							Select a speech to practice
						</p>
					</div>
					
					{speeches.length === 0 ? (
						<div className="w-full rounded-md border-2 border-dashed border-gray-300 p-6 my-5 text-center">
							<p className="text-gray-500 mb-4">No speeches found</p>
							<Link 
								href="/speeches/new"
								className="inline-flex items-center bg-black text-white px-4 py-2 rounded-md font-medium hover:bg-gray-800"
							>
								Create Your First Speech
							</Link>
						</div>
					) : (
						<select
							value={selectedSpeechId}
							onChange={e => setSelectedSpeechId(e.target.value)}
							className="w-full rounded-md border-gray-300 shadow-sm focus:border-black focus:ring-black my-5 px-3 py-2"
						>
							<option value="">Select a speech...</option>
							{speeches.map(speech => (
								<option key={speech.id} value={speech.id}>
									{speech.title} ({speech.context})
								</option>
							))}
						</select>
					)}

					{speeches.length > 0 && (
						<div className="text-center mb-4">
							<Link 
								href="/speeches"
								className="text-blue-600 hover:text-blue-800 text-sm font-medium"
							>
								Manage all speeches →
							</Link>
						</div>
					)}

					{/* File Upload Section */}
					<div className="flex mt-10 items-center space-x-3">
						<Image
							src="/1-black.png"
							width={30}
							height={30}
							alt="upload icon"
							className="mb-5 sm:mb-0"
						/>
						<p className="text-left font-medium">
							Upload your voice recording{" "}
							<span className="text-slate-500">(WAV/MP3)</span>.
						</p>
					</div>
					<input
						type="file"
						accept="audio/*"
						className="w-full rounded-md border-gray-300 shadow-sm focus:border-black focus:ring-black my-5 px-3 py-2"
						onChange={e => setAudioFile(e.target.files?.[0] || null)}
					/>

					{loading ? (
						<button
							className="bg-black rounded-xl text-white font-medium px-4 py-2 sm:mt-10 mt-8 hover:bg-black/80 w-full"
							disabled
						>
							<LoadingDots color="white" style="large" />
						</button>
					) : (
						<button
							className="bg-black rounded-xl text-white font-medium px-4 py-2 sm:mt-10 mt-8 hover:bg-black/80 w-full"
							onClick={() => handleAnalyseSpeech()}
						>
							Analyse My Speach
						</button>
					)}
				</div>
				<Toaster
					position="top-center"
					reverseOrder={false}
					toastOptions={{ duration: 2000 }}
				/>
				<hr className="h-px bg-gray-700 border-1 dark:bg-gray-700" />

				{/* Results Section */}
				<div className="mt-8 grid gap-6 max-w-xl w-full">

					<div>
						<label className="block text-left font-medium mb-2 text-slate-700">
							Transcript
						</label>
						<textarea
							readOnly
							rows={3}
							className="w-full rounded-md border-gray-300 shadow-sm focus:border-black focus:ring-black my-5 px-3 py-2 bg-gray-100 text-gray-700 mb-4"
							value={transcript}
							placeholder="Filler word analysis will appear here."
						/>
					</div>
					{/* Filler Word Count */}
					<div>
						<label className="block text-left font-medium mb-2 text-slate-700">
							Filler Words
						</label>
						{fillerWords && typeof fillerWords === "object" && fillerWords.fillers ? (
							<div className="w-full bg-white rounded-md shadow-sm p-4 mb-4">
								<FillerWordsChart fillerWords={fillerWords} />
							</div>
						) : (
							<textarea
								readOnly
								rows={6}
								className="w-full rounded-md border-gray-300 shadow-sm focus:border-black focus:ring-black my-5 px-3 py-2 bg-gray-100 text-gray-700 mb-4"
								value={typeof fillerWords === "string" ? fillerWords : ""}
								placeholder="Filler words and grammar mistakes analysis will appear here."
							/>
						)}
					</div>
					{/* Recommendations */}
					<div>
						<label className="block text-left font-medium mb-2 text-slate-700">
							Feedback and Recommendations
						</label>
						{recommendations ?
							<div className="w-full rounded-md border-gray-300 shadow-sm focus:border-black focus:ring-black my-5 px-3 py-2 bg-gray-100 text-gray-700 mb-4 prose prose-slate max-w-none text-left overflow-auto">
								<ReactMarkdown>{recommendations}</ReactMarkdown>
							</div>
							:
							<textarea
								readOnly
								rows={15}
								className="w-full rounded-md border-gray-300 shadow-sm focus:border-black focus:ring-black my-5 px-3 py-2 bg-gray-100 text-gray-700 mb-4"
								// value={recommendations}
								placeholder="Feedback and recommendations will appear here."
							/>

						}
					</div>
					{/* Delivery Metrics */}
					{deliveryMetrics && (
						<DeliveryMetricsTable metrics={deliveryMetrics} />
					)}
				</div>
			</main>
		</div>
	);
}
