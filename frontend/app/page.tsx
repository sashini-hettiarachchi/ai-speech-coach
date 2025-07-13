"use client";

import Image from "next/image";
import { useRef, useState } from "react";
import { Toaster, toast } from "react-hot-toast";
import Footer from "../components/Footer";
import Header from "../components/Header";
import LoadingDots from "../components/LoadingDots";
import axios from "axios";
import ReactMarkdown from "react-markdown";

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [fillerWords, setFillerWords] = useState("");
  const [recommendations, setRecommendations] = useState("");
  const [transcript, setTranscript] = useState("");

  const bioRef = useRef<null | HTMLDivElement>(null);

  const handleAnalyseSpeech = async () => {
    setLoading(true);
    try {
      const response = await axios.post("http://localhost:5000/api/v1/analyze");
      // If you need to send a file, use FormData and pass as second argument
      // const response = await axios.post("http://localhost:5000/api/v1/analyze", formData);
      const data = response.data;
      console.log(data);
      // Example: set results to state variables
      setFillerWords(data.fillers);
      setRecommendations(data.recommendations);
      setTranscript(data.transcript);
    } catch (error) {
      toast.error("Error analyzing speech");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex max-w-5xl mx-auto flex-col items-center justify-center py-2 min-h-screen">
      <Header />
      <main className="flex flex-1 w-full flex-col items-center justify-center text-center px-4 mt-12 sm:mt-20">
        <h1 className="sm:text-6xl text-4xl max-w-[708px] font-bold text-slate-900">
          Improve your public speaking by uploading a voice recording
        </h1>

        <div className="max-w-xl w-full">
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
          />

          {/* Voice Recording Section */}
          <div className="flex mt-6 items-center space-x-3">
            <Image
              src="/2-black.png"
              width={30}
              height={30}
              alt="mic icon"
            />
            <p className="text-left font-medium">Or record your voice here.</p>
          </div>
          <div className="flex flex-col items-center my-5">
            <button
              className="bg-black rounded-xl text-white font-medium px-4 py-2 hover:bg-black/80 mb-2"
            // onClick={handleRecord} // Add recording logic as needed
            >
              Start Recording
            </button>
            <span className="text-xs text-gray-500">
              Recording will use your device microphone.
            </span>
          </div>

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
              Filler Words and Grammar Mistakes Analysis
            </label>
            <textarea
              readOnly
              rows={6}
              className="w-full rounded-md border-gray-300 shadow-sm focus:border-black focus:ring-black my-5 px-3 py-2 bg-gray-100 text-gray-700 mb-4"
              value={fillerWords}
              placeholder="Filler words and grammar mistakes analysis will appear here."
            />
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
        </div>
      </main>
      <Footer />
    </div>
  );
}
