"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Cpu, Database, Search, ShieldCheck, Activity, BarChart2 } from "lucide-react";

export const Header: React.FC = () => {
  const pathname = usePathname();

  const navItems = [
    { label: "RESEARCH", href: "/", icon: Cpu },
    { label: "DISCOVERY", href: "/discovery", icon: Search },
    { label: "ENTITIES", href: "/entities", icon: Database },
    { label: "SOURCES", href: "/sources", icon: ShieldCheck },
    { label: "EVALUATION", href: "/eval", icon: BarChart2 },
  ];

  return (
    <header className="sticky top-0 z-50 bg-[#0a0d12]/95 backdrop-blur-md border-b border-[#232838]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Identity */}
          <div className="flex items-center space-x-3">
            <div className="w-2.5 h-2.5 rounded-full bg-[#ffb627] shadow-[0_0_10px_#ffb627] animate-pulse" />
            <Link href="/" className="flex items-baseline space-x-2 font-mono tracking-wider">
              <span className="font-bold text-lg text-[#eceff3]">COSMOHUB</span>
              <span className="text-xs text-[#ffb627] uppercase tracking-widest font-semibold">
                INTELLIGENCE ENGINE
              </span>
            </Link>
          </div>

          {/* Navigation Links */}
          <nav className="flex space-x-1 sm:space-x-4">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center space-x-2 px-3 py-1.5 rounded-md text-xs font-mono tracking-wider transition-colors ${
                    isActive
                      ? "bg-[#171c27] text-[#ffb627] border border-[#8a6a2a]"
                      : "text-[#8891a3] hover:text-[#eceff3] hover:bg-[#12161f]"
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>

          {/* System Status Pill */}
          <div className="hidden md:flex items-center space-x-2 bg-[#12161f] border border-[#232838] px-3 py-1 rounded text-[11px] font-mono text-[#4ce0c6]">
            <Activity className="w-3 h-3 text-[#4ce0c6] animate-pulse" />
            <span>HYBRID RETRIEVAL ACTIVE</span>
          </div>
        </div>
      </div>
    </header>
  );
};
