"use client";
import { useUser } from  '@auth0/nextjs-auth0';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import Link from 'next/link';

export default function UserPage() {
  const { user, isLoading } = useUser();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/auth/login');
    }
  }, [user, isLoading, router]);

  if (isLoading || !user) return <div>Loading...</div>;

  return (
    <div className="max-w-4xl mx-auto mt-10 p-6 space-y-8">
      {/* Profile Information */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold mb-4">User Profile</h2>
        <div className="flex items-center space-x-4">
          <img src={user.picture || "/default-user.png"} alt="User" className="w-16 h-16 rounded-full" />
          <div>
            <div className="font-medium text-lg">{user.name}</div>
            <div className="text-gray-600">{user.email}</div>
          </div>
        </div>
      </div>

      {/* Profile Sections */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Anxiety Assessments */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-xl font-semibold mb-4 text-gray-900">Public Speaking Anxiety Assessments</h3>
          <p className="text-gray-600 mb-4">
            Track your progress with standardized anxiety assessments before and after using the speech coach.
          </p>
          <Link 
            href="/profile/assessments"
            className="inline-block px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            View Assessments
          </Link>
        </div>

        {/* Speech Dashboard */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-xl font-semibold mb-4 text-gray-900">Speech Dashboard</h3>
          <p className="text-gray-600 mb-4">
            Manage your speeches, view practice sessions, and track your speaking performance over time.
          </p>
          <Link 
            href="/dashboard"
            className="inline-block px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
          >
            Go to Dashboard
          </Link>
        </div>

        {/* Speeches */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-xl font-semibold mb-4 text-gray-900">My Speeches</h3>
          <p className="text-gray-600 mb-4">
            Create and manage your speech topics, practice sessions, and get detailed feedback.
          </p>
          <Link 
            href="/speeches"
            className="inline-block px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors"
          >
            Manage Speeches
          </Link>
        </div>

        {/* Account Settings */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-xl font-semibold mb-4 text-gray-900">Account Settings</h3>
          <p className="text-gray-600 mb-4">
            Update your profile information and manage your account preferences.
          </p>
          <a 
            href="/api/auth/logout"
            className="inline-block px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
          >
            Sign Out
          </a>
        </div>
      </div>
    </div>
  );
}