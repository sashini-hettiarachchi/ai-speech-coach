'use client';

import Link from "next/link";
import Github from "./GitHub";
import { useUser } from '@auth0/nextjs-auth0/client';

export default function Header() {
  const { user, isLoading } = useUser();

  return (
    <header className="flex flex-col w-full mt-5 border-b-2 pb-7 sm:px-4 px-2">
      <div className="flex items-center space-x-3 justify-between">
        <div className="flex items-center space-x-3">
          <img
            alt="header text"
            src="/spech.png"
            className="sm:w-9 sm:h-9 w-8 h-8"
          />
          <h1 className="sm:text-3xl text-2xl font-bold ml-2 tracking-tight">
            SpeachCoach.ai
          </h1>
        </div>
        {!isLoading && user ? (
          <div className="flex items-center space-x-3">
            <Link href="/dashboard">
              <button className="bg-gray-100 text-black px-3 py-1 rounded font-medium hover:bg-gray-200 transition">Dashboard</button>
            </Link>
            <Link href="/speeches">
              <button className="bg-gray-100 text-black px-3 py-1 rounded font-medium hover:bg-gray-200 transition">Speeches</button>
            </Link>
            <Link href="/admin">
              <button className="bg-purple-100 text-purple-800 px-3 py-1 rounded font-medium hover:bg-purple-200 transition">Admin</button>
            </Link>
            <Link href="/profile">
              <button className="bg-gray-100 text-black px-3 py-1 rounded font-medium hover:bg-gray-200 transition">Profile</button>
            </Link>
            <Link href="/auth/logout">
              <button className="bg-black text-white px-4 py-2 rounded-md font-medium hover:bg-black/80 transition">Logout</button>
            </Link>
          </div>
        ) : (
          <Link href="/auth/login">
            <button className="bg-black text-white px-4 py-2 rounded-md font-medium hover:bg-black/80 transition">
              {isLoading ? 'Loading...' : 'Login'}
            </button>
          </Link>
        )}
      </div>
      <a
        href="https://www.flaticon.com/free-icons/spech"
        title="spech icons"
        className="text-[10px] mt-1 self-start text-gray-400"
        style={{ lineHeight: 1 }}
      >
        Spech icons created by Aranagraphics - Flaticon
      </a>
    </header>
  );
}
