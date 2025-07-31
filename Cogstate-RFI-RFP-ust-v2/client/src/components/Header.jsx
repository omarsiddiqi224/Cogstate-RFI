import React from "react";
import { Search, Bell, HelpCircle, User, Bolt } from "lucide-react";

export default function Header() {
  return (
    <header className="bg-white text-black px-6 py-3 flex justify-between items-center border-b">
      {/* Logo / brand */}
      <div className="flex items-center gap-3">
        <div className="w-32 bg-white rounded flex">
        <img src="/logo-main.svg" alt="Cogstate Logo" className="logo" />
        </div>
      </div>

      {/* Right side icons and user */}
      <div className="flex items-center gap-4">
        <Search size={20} strokeWidth={1.5} className="cursor-pointer text-header-icon hover:text-gray-300" />
        <div className="relative">
          <Bell size={20} strokeWidth={1.5} className="cursor-pointer text-header-icon hover:text-gray-300" />
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center">1</span>
        </div>
        <Bolt size={20} strokeWidth={1.5} className="cursor-pointer text-header-icon hover:text-gray-300" />
        <HelpCircle size={20} strokeWidth={1.5} className="cursor-pointer text-header-icon hover:text-gray-300" />
        <div className="flex items-center gap-2 cursor-pointer hover:text-gray-300">
          <div className="w-8 h-8 bg-orange-400 rounded-full flex items-center justify-center">
            <span className="text-white text-sm font-medium">RC</span>
          </div>
          <span className="text-sm text-primary">RFP_Coordinator</span>
        </div>
      </div>
    </header>
  );
}