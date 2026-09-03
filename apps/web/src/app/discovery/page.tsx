"use client";

import React, { useEffect, useState } from "react";
import { fetchSources } from "@/lib/api";
import { Source } from "@/lib/types";
import { Search, FileText, Globe, Clock, Hash, CheckCircle2 } from "lucide-react";

export default function DiscoveryPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    fetchSources()
      .then((data) => setSources(data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const filteredSources = sources.filter((s) =>
    s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    s.source_type.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6 font-mono">
      <div className="flex items-center justify-between pb-4 border-b border-[#232838]">
        <div>
          <h1 className="text-2xl font-bold font-display text-[#eceff3]">KNOWLEDGE DISCOVERY & SOURCE REGISTRY</h1>
          <p className="text-xs text-[#8891a3] font-sans mt-1">
            Browse indexed space economy datasets, document hashes, and provenance trails.
          </p>
        </div>
        <div className="bg-[#171c27] border border-[#232838] px-3 py-1.5 rounded text-xs text-[#ffb627]">
          {sources.length} REGISTERED SOURCES
        </div>
      </div>

      {/* Filter Bar */}
      <div className="relative">
        <Search className="w-4 h-4 text-[#ffb627] absolute left-3 top-3" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Filter sources by name or type..."
          className="w-full bg-[#12161f] border border-[#232838] focus:border-[#ffb627] rounded-lg py-2 pl-9 pr-4 text-xs text-[#eceff3] focus:outline-none"
        />
      </div>

      {/* Grid of Sources */}
      {loading ? (
        <div className="p-8 text-center text-xs text-[#8891a3]">LOADING SOURCE REGISTRY...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredSources.map((src) => (
            <div
              key={src.source_id}
              className="bg-[#12161f] border border-[#232838] p-4 rounded-lg space-y-3 hover:border-[#8a6a2a] transition-colors"
            >
              <div className="flex items-center justify-between">
                <span className="px-2 py-0.5 rounded bg-[#171c27] border border-[#8a6a2a] text-[10px] text-[#ffb627] font-bold uppercase">
                  {src.source_type}
                </span>
                <span className="flex items-center gap-1 text-[10px] text-[#4ce0c6]">
                  <CheckCircle2 className="w-3 h-3" />
                  {src.status.toUpperCase()}
                </span>
              </div>

              <div>
                <h3 className="text-sm font-bold text-[#eceff3] font-sans truncate">{src.name}</h3>
                <div className="text-[10.5px] text-[#8891a3] truncate mt-1 flex items-center gap-1">
                  <Globe className="w-3 h-3 text-[#ffb627]" />
                  <span>{src.url_or_path}</span>
                </div>
              </div>

              <div className="pt-2 border-t border-[#232838] text-[10.5px] text-[#8891a3] space-y-1">
                <div className="flex justify-between">
                  <span>DOCUMENTS INDEXED:</span>
                  <b className="text-[#eceff3]">{src.document_count}</b>
                </div>
                <div className="flex justify-between">
                  <span>TRUST LEVEL:</span>
                  <b className="text-[#ffb627]">{(src.trust_level * 100).toFixed(0)}%</b>
                </div>
                <div className="flex justify-between truncate">
                  <span>CONTENT HASH:</span>
                  <b className="text-[#4ce0c6]">{src.last_content_hash?.slice(0, 12) || "N/A"}...</b>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
