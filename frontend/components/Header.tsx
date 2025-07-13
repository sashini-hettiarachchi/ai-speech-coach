import Link from "next/link";
import Github from "./GitHub";

export default function Header() {
  return (
    <header className="flex flex-col w-full mt-5 border-b-2 pb-7 sm:px-4 px-2">
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
