"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useUser } from '@auth0/nextjs-auth0';
import { useRouter, useParams } from 'next/navigation';
import Link from "next/link";
import { toast, Toaster } from "react-hot-toast";
import { speechApi, sessionApi } from "../../../../../lib/api";
import LoadingDots from "../../../../../components/LoadingDots";

interface Speech {
  id: string;
  title: string;
  description: string;
  goal: string;
  audience_description: string;
  key_points: string;
  self_improvement_goal: string;
  context: string;
  with_context: boolean;
  completed: boolean;
}

export default function NewSessionPage() {
  const { user, isLoading } = useUser();
  const router = useRouter();
  const params = useParams();
  const speechId = params.id as string;
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [speech, setSpeech] = useState<Speech | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [sessionTitle, setSessionTitle] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [audioPreviewUrl, setAudioPreviewUrl] = useState<string | null>(null);

  // Redirect to login if not authenticated
  if (!isLoading && !user) {
    router.push('/api/auth/login');
    return <div>Redirecting to login...</div>;
  }

  useEffect(() => {
    if (user && speechId) {
      loadSpeechData();
    }
  }, [user, speechId]);

  const loadSpeechData = async () => {
    try {
      setLoading(true);
      const speechData = await speechApi.getSpeech(speechId);
      setSpeech(speechData);
    } catch (error) {
      console.error("Error loading speech data:", error);
      toast.error("Failed to load speech data");
      router.push('/speeches');
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (file: File) => {
    const maxSize = 100 * 1024 * 1024; // 100MB
    const allowedTypes = [
      'audio/mpeg', 'audio/wav', 'audio/mp3', 'audio/mp4', 'audio/ogg',
      'video/mp4', 'video/mpeg', 'video/quicktime', 'video/x-msvideo'
    ];

    if (file.size > maxSize) {
      toast.error("File size must be less than 100MB");
      return;
    }

    if (!allowedTypes.some(type => file.type.includes(type.split('/')[1]))) {
      toast.error("Please select an audio or video file (MP3, WAV, MP4, MOV, AVI)");
      return;
    }

    setSelectedFile(file);

    // Create preview URL for audio/video
    const previewUrl = URL.createObjectURL(file);
    setAudioPreviewUrl(previewUrl);

    toast.success("File selected successfully!");
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedFile) {
      toast.error("Please select an audio or video file");
      return;
    }

    setUploading(true);

    try {
      // Create session first
      const result = await sessionApi.analyzeAndCreateSession(speechId, selectedFile, sessionTitle.trim() || undefined);

      toast.success("Session created and analysis completed!");
      router.push(`/speeches/${speechId}/sessions/${result.session_id}`);
    } catch (error) {
      console.error("Error creating session:", error);
      toast.error("Failed to create session. Please try again.");
    } finally {
      setUploading(false);
    }
  };

  const resetFile = () => {
    setSelectedFile(null);
    
    // Clean up preview URL
    if (audioPreviewUrl) {
      URL.revokeObjectURL(audioPreviewUrl);
      setAudioPreviewUrl(null);
    }
    
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };


  // Clean up preview URL when component unmounts
  useEffect(() => {
    return () => {
      if (audioPreviewUrl) {
        URL.revokeObjectURL(audioPreviewUrl);
      }
    };
  }, [audioPreviewUrl]);

  if (isLoading || loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  if (!speech) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="text-lg">Speech not found</div>
      </div>
    );
  }

  if (speech.completed) {
    return (
      <div className="flex max-w-2xl mx-auto flex-col py-2 min-h-screen">
        <main className="flex flex-1 w-full flex-col px-4 mt-12 sm:mt-20">
          <div className="flex items-center space-x-4 mb-6">
            <Link
              href={`/speeches/${speechId}`}
              className="text-blue-600 hover:text-blue-800 font-medium"
            >
              ← Back to Speech
            </Link>
          </div>
          
          <div className="text-center py-12">
            <div className="bg-green-50 border border-green-200 rounded-lg p-8">
              <div className="flex justify-center mb-4">
                <svg className="h-12 w-12 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-green-800 mb-2">
                Speech Completed
              </h3>
              <p className="text-green-700 mb-4">
                This speech has been marked as completed. You cannot create new practice sessions for completed speeches.
              </p>
              <Link
                href={`/speeches/${speechId}`}
                className="inline-flex items-center bg-green-600 text-white px-4 py-2 rounded-md font-medium hover:bg-green-700 transition-colors"
              >
                View Speech Details
              </Link>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="flex max-w-2xl mx-auto flex-col py-2 min-h-screen">
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

        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-slate-900 mb-2">
            New Practice Session
          </h1>
          <p className="text-gray-600">
            For: <span className="font-medium">{speech.title}</span>
          </p>
        </div>

        {/* Speech Information Card */}
        <div className="bg-gradient-to-r from-slate-50 to-blue-50 border border-slate-200 rounded-lg p-6 mb-8">
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-10 h-10 bg-blue-500 text-white rounded-full flex items-center justify-center">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900">{speech.title}</h2>
              <div className="flex items-center space-x-4 text-sm text-slate-600">
                {speech.context && (
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
                    {speech.context.charAt(0).toUpperCase() + speech.context.slice(1)}
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="space-y-4">
            {/* Description */}
            {speech.description && (
              <div>
                <h3 className="text-sm font-semibold text-slate-700 mb-2 flex items-center">
                  <svg className="w-4 h-4 mr-2 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h7" />
                  </svg>
                  Description
                </h3>
                <p className="text-slate-600 text-sm leading-relaxed bg-white/50 rounded-md p-3 border border-slate-200">
                  {speech.description}
                </p>
              </div>
            )}

            {/* Goal */}
            {speech.goal && (
              <div>
                <h3 className="text-sm font-semibold text-slate-700 mb-2 flex items-center">
                  <svg className="w-4 h-4 mr-2 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                  </svg>
                  Goal & Purpose
                </h3>
                <p className="text-slate-600 text-sm leading-relaxed bg-white/50 rounded-md p-3 border border-slate-200">
                  {speech.goal}
                </p>
              </div>
            )}

            {/* Audience Description */}
            {speech.audience_description && (
              <div>
                <h3 className="text-sm font-semibold text-slate-700 mb-2 flex items-center">
                  <svg className="w-4 h-4 mr-2 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 01-3 0m3 0V5.372a1.5 1.5 0 00-.83-1.342l-2.66-1.33a1.5 1.5 0 00-1.34 0l-2.66 1.33A1.5 1.5 0 007.5 5.372V8.5" />
                  </svg>
                  Target Audience
                </h3>
                <p className="text-slate-600 text-sm leading-relaxed bg-white/50 rounded-md p-3 border border-slate-200">
                  {speech.audience_description}
                </p>
              </div>
            )}

            {/* Key Points */}
            {speech.key_points && (
              <div>
                <h3 className="text-sm font-semibold text-slate-700 mb-2 flex items-center">
                  <svg className="w-4 h-4 mr-2 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                  </svg>
                  Key Points & Outline
                </h3>
                <div className="text-slate-600 text-sm leading-relaxed bg-white/50 rounded-md p-3 border border-slate-200">
                  {speech.key_points.split('\n').map((point, index) => (
                    <div key={index} className="mb-1">
                      {point.trim() && (
                        <span className="flex items-start">
                          <span className="text-blue-500 mr-2 mt-1">•</span>
                          <span>{point.trim()}</span>
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Self Improvement Goal */}
            {speech.self_improvement_goal && (
              <div>
                <h3 className="text-sm font-semibold text-slate-700 mb-2 flex items-center">
                  <svg className="w-4 h-4 mr-2 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  What You Want to Improve
                </h3>
                <p className="text-slate-600 text-sm leading-relaxed bg-white/50 rounded-md p-3 border border-slate-200">
                  {speech.self_improvement_goal}
                </p>
              </div>
            )}

            {/* Quick Tips */}
            <div className="bg-amber-50 border border-amber-200 rounded-md p-3">
              <h3 className="text-sm font-semibold text-amber-800 mb-2 flex items-center">
                <svg className="w-4 h-4 mr-2 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                Practice Tips
              </h3>
              <ul className="text-xs text-amber-700 space-y-1">
                <li>• Review your key points before recording</li>
                <li>• Keep your target audience in mind</li>
                <li>• Focus on your improvement goals</li>
                <li>• Practice with confidence and clarity</li>
                <li>• Remember the context: <strong>{speech.context}</strong></li>
              </ul>
            </div>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Session Title (Optional) */}
          <div>
            <label htmlFor="sessionTitle" className="block text-sm font-medium text-gray-700 mb-2">
              Session Title (Optional)
            </label>
            <input
              type="text"
              id="sessionTitle"
              value={sessionTitle}
              onChange={(e) => setSessionTitle(e.target.value)}
              placeholder="e.g., Practice Run #1, Rehearsal for Conference, etc."
              className="w-full rounded-md border-gray-300 shadow-sm focus:border-black focus:ring-black px-3 py-2"
            />
            <p className="text-sm text-gray-500 mt-1">
              Give your session a name to help you identify it later
            </p>
          </div>

          {/* File Upload Area */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Upload Audio or Video *
            </label>

            {!selectedFile ? (
              <div
                className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${dragOver
                    ? 'border-black bg-gray-50'
                    : 'border-gray-300 hover:border-gray-400'
                  }`}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
              >
                <div className="space-y-4">
                  <div className="mx-auto w-12 h-12 text-gray-400">
                    <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                  </div>

                  <div>
                    <p className="text-lg font-medium text-gray-900">
                      Drop your file here, or{" "}
                      <button
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                        className="text-blue-600 hover:text-blue-800 underline"
                      >
                        browse
                      </button>
                    </p>
                    <p className="text-sm text-gray-500 mt-2">
                      Supports MP3, WAV, MP4, MOV, AVI files up to 100MB
                    </p>
                  </div>
                </div>

                <input
                  ref={fileInputRef}
                  type="file"
                  accept="audio/*,video/*"
                  onChange={handleFileInputChange}
                  className="hidden"
                />
              </div>
            ) : (
              <div className="border-2 border-green-300 bg-green-50 rounded-lg p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                      <svg className="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{selectedFile.name}</p>
                      <p className="text-sm text-gray-500">
                        {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={resetFile}
                    className="text-red-600 hover:text-red-800 font-medium"
                  >
                    Remove
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Audio/Video Preview */}
          {selectedFile && audioPreviewUrl && (
            <div className="mt-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Preview Your Recording
              </label>
              <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4 border-2 border-blue-200">
                <div className="flex items-center space-x-3 mb-3">
                  <div className="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center">
                    {selectedFile.type.startsWith('video/') ? '🎥' : '🎵'}
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">
                      {selectedFile.type.startsWith('video/') ? 'Video Recording' : 'Audio Recording'}
                    </h3>
                    <p className="text-sm text-gray-600">{selectedFile.name}</p>
                  </div>
                </div>

                {selectedFile.type.startsWith('video/') ? (
                  <video
                    controls
                    className="w-full max-h-64 rounded-lg"
                    src={audioPreviewUrl}
                    preload="metadata"
                    style={{ backgroundColor: '#f3f4f6' }}
                  >
                    Your browser does not support the video tag.
                  </video>
                ) : (
                  <audio
                    controls
                    className="w-full"
                    src={audioPreviewUrl}
                    preload="metadata"
                    style={{
                      filter: 'sepia(0) hue-rotate(200deg) saturate(1.2)',
                      borderRadius: '8px'
                    }}
                  >
                    Your browser does not support the audio tag.
                  </audio>
                )}

                <div className="flex items-center justify-between mt-3">
                  <div className="text-xs text-gray-500">
                    💡 Listen to your recording to make sure it's clear and complete
                  </div>
                  <button
                    type="button"
                    onClick={resetFile}
                    className="text-red-600 hover:text-red-800 hover:underline font-medium text-sm"
                  >
                    🔄 Choose Different File
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Submit Button */}
          <div className="pt-4">
            {uploading ? (
              <div className="w-full bg-gray-400 text-white font-medium py-4 px-4 rounded-md cursor-not-allowed flex items-center justify-center">
                <LoadingDots color="white" />
                <span className="ml-2">Creating session and analyzing speech...</span>
              </div>
            ) : (
              <button
                type="submit"
                disabled={!selectedFile}
                className={`w-full font-medium py-4 px-4 rounded-md transition-colors ${selectedFile ? 'bg-green-600 text-white hover:bg-green-700' : 'bg-gray-300 text-gray-500 cursor-not-allowed'}`}
              >
                {!selectedFile ? 'Select File First' : '🚀 Start AI Analysis'}
              </button>
            )}

            {selectedFile && (
              <p className="text-sm text-gray-600 text-center mt-2">
                Please complete your self-rating above to enable the analysis button
              </p>
            )}
          </div>
        </form>

        {/* Help Text */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-6">
          <h3 className="font-medium text-blue-900 mb-2">Tips for better analysis:</h3>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• Record in a quiet environment with minimal background noise</li>
            <li>• Speak clearly and at a normal pace</li>
            <li>• Keep your recording device at a consistent distance</li>
            <li>• Aim for recordings between 1-5 minutes for best results</li>
          </ul>
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
