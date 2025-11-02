"use client";

import { useState, useEffect } from "react";
import { useUser } from '@auth0/nextjs-auth0';
import { useRouter, useParams } from 'next/navigation';
import Link from "next/link";
import { toast, Toaster } from "react-hot-toast";
import { speechApi } from "../../../../lib/api";
import PRPSAAssessment from "../../../../components/PRPSAAssessment";
import PRPSAResults from "../../../../components/PRPSAResults";

interface Speech {
  id: string;
  title: string;
  prpsa_completed: boolean;
  completed: boolean;
}

export default function PRPSAPage() {
  const { user, isLoading } = useUser();
  const router = useRouter();
  const params = useParams();
  const speechId = params.id as string;

  const [speech, setSpeech] = useState<Speech | null>(null);
  const [loading, setLoading] = useState(true);
  const [prpsa, setPrpsa] = useState<any>(null);
  const [prpsaLoading, setPrpsaLoading] = useState(false);
  const [showResults, setShowResults] = useState(false);

  // Redirect to login if not authenticated
  if (!isLoading && !user) {
    router.push('/api/auth/login');
    return <div>Redirecting to login...</div>;
  }

  useEffect(() => {
    if (user && speechId) {
      loadData();
    }
  }, [user, speechId]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [speechData, prpsaData] = await Promise.all([
        speechApi.getSpeech(speechId),
        speechApi.getPRPSA(speechId)
      ]);
      
      setSpeech(speechData);
      
      if (prpsaData.completed) {
        setPrpsa(prpsaData.prpsa);
        setShowResults(true);
      }
    } catch (error) {
      console.error("Error loading data:", error);
      toast.error("Failed to load data");
      router.push('/speeches');
    } finally {
      setLoading(false);
    }
  };

  const handlePRPSAComplete = async (responses: Record<string, number>) => {
    try {
      setPrpsaLoading(true);
      const result = await speechApi.submitPRPSA(speechId, responses);
      
      setPrpsa(result.prpsa);
      setSpeech(result.speech);
      setShowResults(true);
      
      toast.success("PRPSA assessment completed successfully!");
    } catch (error: any) {
      console.error("Error submitting PRPSA:", error);
      toast.error(error.response?.data?.error || "Failed to submit assessment");
    } finally {
      setPrpsaLoading(false);
    }
  };

  const handleCancel = () => {
    router.push(`/speeches/${speechId}`);
  };

  const handleContinueToCompletion = () => {
    router.push(`/speeches/${speechId}?showCompletion=true`);
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
              <h3 className="text-lg font-medium text-green-800 mb-2">
                Speech Already Completed
              </h3>
              <p className="text-green-700 mb-4">
                This speech has already been completed. You cannot modify the PRPSA assessment for completed speeches.
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
    <div className="min-h-screen bg-gray-50">
      <main className="py-8">
        {/* Navigation */}
        <div className="max-w-4xl mx-auto px-6 mb-6">
          <div className="flex items-center space-x-4">
            <Link
              href={`/speeches/${speechId}`}
              className="text-blue-600 hover:text-blue-800 font-medium"
            >
              ← Back to Speech
            </Link>
            <span className="text-gray-400">|</span>
            <span className="text-gray-600">
              <strong>{speech.title}</strong> - PRPSA Assessment
            </span>
          </div>
        </div>

        {showResults ? (
          <div className="max-w-4xl mx-auto px-6">
            <PRPSAResults prpsa={prpsa} />
            
            {/* Action Buttons */}
            <div className="mt-8 text-center">
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Next Steps
                </h3>
                <p className="text-gray-600 mb-6">
                  You have successfully completed the PRPSA assessment. You can now proceed to complete your speech.
                </p>
                <div className="flex justify-center space-x-4">
                  <Link
                    href={`/speeches/${speechId}`}
                    className="px-6 py-2 bg-gray-600 text-white rounded-md font-medium hover:bg-gray-700 transition-colors"
                  >
                    Back to Speech
                  </Link>
                  <button
                    onClick={handleContinueToCompletion}
                    className="px-6 py-2 bg-green-600 text-white rounded-md font-medium hover:bg-green-700 transition-colors"
                  >
                    Complete Speech
                  </button>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <PRPSAAssessment
            speechId={speechId}
            onComplete={handlePRPSAComplete}
            onCancel={handleCancel}
          />
        )}

        <Toaster
          position="top-center"
          reverseOrder={false}
          toastOptions={{ duration: 3000 }}
        />
      </main>
    </div>
  );
}