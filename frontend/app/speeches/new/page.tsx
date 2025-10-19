"use client";

import { useState } from "react";
import { useUser } from '@auth0/nextjs-auth0';
import { useRouter } from 'next/navigation';
import { toast, Toaster } from "react-hot-toast";
import Link from "next/link";
import { speechApi } from "../../../lib/api";

const CONTEXT_OPTIONS = [
  { value: "Academic", label: "Academic" },
  { value: "Storytelling", label: "Storytelling" },
  { value: "Persuasive", label: "Persuasive" }
];

export default function NewSpeech() {
  const { user, isLoading } = useUser();
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    context: "Academic",
    goal: ""
  });

  // Redirect to login if not authenticated
  if (!isLoading && !user) {
    router.push('/api/auth/login');
    return <div>Redirecting to login...</div>;
  }

  if (isLoading) {
    return <div className="flex justify-center items-center min-h-screen">Loading...</div>;
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.title.trim()) {
      toast.error("Please enter a title for your speech");
      return;
    }

    if (!formData.description.trim()) {
      toast.error("Please enter a description for your speech");
      return;
    }

    if (!formData.goal.trim()) {
      toast.error("Please enter a goal for your speech");
      return;
    }

    setLoading(true);
    
    try {
      const speech = await speechApi.createSpeech(formData);
      toast.success("Speech created successfully!");
      router.push(`/speeches/${speech.id}`);
    } catch (error) {
      console.error("Error creating speech:", error);
      toast.error("Failed to create speech. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex max-w-2xl mx-auto flex-col items-center justify-center py-2 min-h-screen">
      <main className="flex flex-1 w-full flex-col items-center justify-center text-center px-4 mt-12 sm:mt-20">
        <div className="flex items-center space-x-3 mb-8">
          <Link href="/speeches" className="text-blue-600 hover:text-blue-800">
            ← Back to Speeches
          </Link>
        </div>

        <h1 className="sm:text-6xl text-4xl max-w-[708px] font-bold text-slate-900 mb-8">
          Create New Speech
        </h1>

        <form onSubmit={handleSubmit} className="w-full max-w-xl space-y-6">
          {/* Title Field */}
          <div className="text-left">
            <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
              Speech Title *
            </label>
            <input
              type="text"
              id="title"
              name="title"
              value={formData.title}
              onChange={handleInputChange}
              placeholder="Enter a title for your speech"
              className="w-full rounded-md border-gray-300 shadow-sm focus:border-black focus:ring-black px-3 py-2"
              required
            />
          </div>

          {/* Description Field */}
          <div className="text-left">
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
              Description *
            </label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleInputChange}
              placeholder="Describe what your speech is about"
              rows={4}
              className="w-full rounded-md border-gray-300 shadow-sm focus:border-black focus:ring-black px-3 py-2"
              required
            />
          </div>

          {/* Context Dropdown */}
          <div className="text-left">
            <label htmlFor="context" className="block text-sm font-medium text-gray-700 mb-2">
              Speech Context *
            </label>
            <select
              id="context"
              name="context"
              value={formData.context}
              onChange={handleInputChange}
              className="w-full rounded-md border-gray-300 shadow-sm focus:border-black focus:ring-black px-3 py-2"
              required
            >
              {CONTEXT_OPTIONS.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <p className="text-sm text-gray-500 mt-1">
              Choose the context that best fits your speech
            </p>
          </div>

          {/* Goal Field */}
          <div className="text-left">
            <label htmlFor="goal" className="block text-sm font-medium text-gray-700 mb-2">
              Speech Goal *
            </label>
            <textarea
              id="goal"
              name="goal"
              value={formData.goal}
              onChange={handleInputChange}
              placeholder="What do you want to achieve with this speech?"
              rows={3}
              className="w-full rounded-md border-gray-300 shadow-sm focus:border-black focus:ring-black px-3 py-2"
              required
            />
            <p className="text-sm text-gray-500 mt-1">
              Describe your objectives and what you want your audience to take away
            </p>
          </div>
          

          {/* Submit Button */}
          <div className="pt-4">
            {loading ? (
              <button
                type="button"
                disabled
                className="w-full bg-gray-400 text-white font-medium py-3 px-4 rounded-md cursor-not-allowed"
              >
                Creating Speech...
              </button>
            ) : (
              <button
                type="submit"
                className="w-full bg-black text-white font-medium py-3 px-4 rounded-md hover:bg-gray-800 transition-colors"
              >
                Create Speech
              </button>
            )}
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
