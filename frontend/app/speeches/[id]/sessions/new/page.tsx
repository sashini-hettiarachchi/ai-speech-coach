"use client";

import { useState, useRef, useEffect } from "react";
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
  context: string;
  goal: string;
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
      // Update the sessionApi to include session title
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
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

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
                className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                  dragOver 
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

          {/* Submit Button */}
          <div className="pt-4">
            {uploading ? (
              <div className="w-full bg-gray-400 text-white font-medium py-4 px-4 rounded-md cursor-not-allowed flex items-center justify-center">
                <LoadingDots color="white" />
                <span className="ml-2">Analyzing speech...</span>
              </div>
            ) : (
              <button
                type="submit"
                disabled={!selectedFile}
                className={`w-full font-medium py-4 px-4 rounded-md transition-colors ${
                  selectedFile
                    ? 'bg-black text-white hover:bg-gray-800'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                }`}
              >
                Start Analysis
              </button>
            )}
          </div>

          {/* Help Text */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="font-medium text-blue-900 mb-2">Tips for better analysis:</h3>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• Record in a quiet environment with minimal background noise</li>
              <li>• Speak clearly and at a normal pace</li>
              <li>• Keep your recording device at a consistent distance</li>
              <li>• Aim for recordings between 1-15 minutes for best results</li>
            </ul>
          </div>
        </form>

        <Toaster
          position="top-center"
          reverseOrder={false}
          toastOptions={{ duration: 3000 }}
        />
      </main>
    </div>
  );
}
