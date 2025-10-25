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
    goal: "",
    audience_description: "",
    key_points: "",
    self_improvement_goal: "",
    context: "Academic"
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

    if (!formData.goal.trim()) {
      toast.error("Please enter a goal/objective for your speech");
      return;
    }

    if (!formData.audience_description.trim()) {
      toast.error("Please describe your audience");
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

          {/* Speech Goal/Objective Field */}
          <div className="text-left">
            <label htmlFor="goal" className="block text-sm font-medium text-gray-700 mb-2">
              Speech Goal / Objective *
            </label>
            <textarea
              id="goal"
              name="goal"
              value={formData.goal}
              onChange={handleInputChange}
              placeholder="What is the main goal of your speech? (e.g., to inform, to inspire, to persuade, to entertain)"
              rows={3}
              className="w-full rounded-md border-gray-300 shadow-sm focus:border-black focus:ring-black px-3 py-2"
              required
            />
            <p className="text-sm text-gray-500 mt-1">
              What are you trying to achieve with this speech?
            </p>
          </div>

          {/* Audience Description Field */}
          <div className="text-left">
            <label htmlFor="audience_description" className="block text-sm font-medium text-gray-700 mb-2">
              Audience Description *
            </label>
            <textarea
              id="audience_description"
              name="audience_description"
              value={formData.audience_description}
              onChange={handleInputChange}
              placeholder="Who is your audience? (e.g., classmates, executives, general public)"
              rows={3}
              className="w-full rounded-md border-gray-300 shadow-sm focus:border-black focus:ring-black px-3 py-2"
              required
            />
            <p className="text-sm text-gray-500 mt-1">
              Describe who you are speaking to
            </p>
          </div>

          {/* Key Points or Outline Field */}
          <div className="text-left">
            <label htmlFor="key_points" className="block text-sm font-medium text-gray-700 mb-2">
              Key Points or Outline
            </label>
            <textarea
              id="key_points"
              name="key_points"
              value={formData.key_points}
              onChange={handleInputChange}
              placeholder="Main Points or Structure (optional, but helps us understand your structure)"
              rows={4}
              className="w-full rounded-md border-gray-300 shadow-sm focus:border-black focus:ring-black px-3 py-2"
            />
            <p className="text-sm text-gray-500 mt-1">
              List 2-3 main points or sections of your speech
            </p>
          </div>

          {/* Self-Improvement Goal Field */}
          <div className="text-left">
            <label htmlFor="self_improvement_goal" className="block text-sm font-medium text-gray-700 mb-2">
              Self-Improvement Goal (Optional)
            </label>
            <textarea
              id="self_improvement_goal"
              name="self_improvement_goal"
              value={formData.self_improvement_goal}
              onChange={handleInputChange}
              placeholder="What skill are you most trying to improve? (e.g., confidence, storytelling, clarity)"
              rows={2}
              className="w-full rounded-md border-gray-300 shadow-sm focus:border-black focus:ring-black px-3 py-2"
            />
            <p className="text-sm text-gray-500 mt-1">
              Pick one or two areas you'd like to focus on improving
            </p>
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
