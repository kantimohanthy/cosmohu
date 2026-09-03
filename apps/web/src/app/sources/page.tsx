"use client";

import React, { useEffect, useState } from "react";
import { fetchSources, triggerIngestion, fetchIngestionJob } from "@/lib/api";
import { Source, IngestionJob } from "@/lib/types";
import { ShieldCheck, Play, RefreshCw, CheckCircle, AlertCircle, FileText } from "lucide-react";

export default function SourcesPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeJob, setActiveJob] = useState<IngestionJob | null>(null);
  const [ingestingSourceId, setIngestingSourceId] = useState<string | null>(null);

  const loadSources = () => {
    setLoading(true);
    fetchSources()
      .then((data) => setSources(data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadSources();
  }, []);

  const handleTriggerIngestion = async (sourceId: string) => {
    setIngestingSourceId(sourceId);
    try {
      const job = await triggerIngestion(sourceId);
      setActiveJob(job);
      // Poll job status
      const interval = setInterval(async () => {
        try {
          const updated = await fetchIngestionJob(job.job_id);
          setActiveJob(updated);
          if (updated.status === "completed" || updated.status === "failed") {
            clearInterval(interval);
            setIngestingSourceId(null);
            loadSources();
          }
        } catch (e) {
          clearInterval(interval);
          setIngestingSourceId(null);
        }
      }, 1000);
    } catch (err: any) {
      alert("Failed to trigger ingestion: " + err.message);
      setIngestingSourceId(null);
    }
  };

  return (
    <div className="space-y-6 font-mono">
      <div className="flex items-center justify-between pb-4 border-b border-[#232838]">
        <div>
          <h1 className="text-2xl font-bold font-display text-[#eceff3]">INGESTION CONSOLE & SOURCE REGISTRY</h1>
          <p className="text-xs text-[#8891a3] font-sans mt-1">
            Manage data crawlers, trigger ingestion pipelines, inspect change detection logs and SHA-256 hashes.
          </p>
        </div>
        <button
          onClick={loadSources}
          className="flex items-center space-x-2 px-3 py-1.5 rounded bg-[#171c27] hover:bg-[#232838] border border-[#232838] text-xs text-[#eceff3] transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>REFRESH</span>
        </button>
      </div>

      {/* Active Ingestion Job Banner */}
      {activeJob && (
        <div className="p-4 bg-[#171c27] border border-[#8a6a2a] rounded-lg space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-[#ffb627] font-bold flex items-center gap-2">
              <Play className="w-3.5 h-3.5 animate-pulse" />
              INGESTION JOB IN PROGRESS: {activeJob.job_id}
            </span>
            <span className="text-[#4ce0c6] uppercase font-bold">{activeJob.status}</span>
          </div>

          <div className="grid grid-cols-4 gap-2 text-[10.5px] text-[#8891a3] pt-2 border-t border-[#232838]">
            <div>DISCOVERED: <b className="text-[#eceff3]">{activeJob.documents_discovered}</b></div>
            <div>PROCESSED: <b className="text-[#eceff3]">{activeJob.documents_processed}</b></div>
            <div>CHUNKS: <b className="text-[#ffb627]">{activeJob.chunks_created}</b></div>
            <div>CONTENT CHANGED: <b className="text-[#4ce0c6]">{activeJob.content_changed ? "YES" : "NO (SKIPPED)"}</b></div>
          </div>
        </div>
      )}

      {/* Sources List */}
      <div className="bg-[#12161f] border border-[#232838] rounded-lg overflow-hidden">
        <div className="p-4 border-b border-[#232838] text-xs font-semibold text-[#ffb627]">
          REGISTERED SOURCES ({sources.length})
        </div>

        <div className="divide-y divide-[#232838]">
          {sources.map((src) => {
            const isIngesting = ingestingSourceId === src.source_id;

            return (
              <div key={src.source_id} className="p-4 flex items-center justify-between hover:bg-[#171c27] transition-colors">
                <div className="space-y-1 max-w-xl">
                  <div className="flex items-center space-x-2">
                    <span className="px-2 py-0.5 rounded bg-[#171c27] border border-[#8a6a2a] text-[10px] text-[#ffb627] font-bold uppercase">
                      {src.source_type}
                    </span>
                    <h4 className="text-sm font-bold text-[#eceff3] font-sans">{src.name}</h4>
                  </div>
                  <div className="text-[10.5px] text-[#8891a3] truncate">{src.url_or_path}</div>
                  <div className="text-[10px] text-[#4ce0c6] truncate">
                    SHA-256 HASH: {src.last_content_hash?.slice(0, 16) || "UNHASHED"}...
                  </div>
                </div>

                <div className="flex items-center space-x-4">
                  <div className="text-right text-[10.5px] text-[#8891a3]">
                    <div>DOCS: <b className="text-[#eceff3]">{src.document_count}</b></div>
                    <div>FREQUENCY: <b className="text-[#ffb627]">{src.crawl_frequency}</b></div>
                  </div>

                  <button
                    onClick={() => handleTriggerIngestion(src.source_id)}
                    disabled={isIngesting}
                    className="flex items-center space-x-2 px-3 py-2 bg-[#ffb627] hover:bg-[#e09e1f] disabled:bg-[#232838] text-[#0a0d12] disabled:text-[#8891a3] font-bold rounded text-xs transition-colors"
                  >
                    <Play className={`w-3 h-3 ${isIngesting ? "animate-spin" : ""}`} />
                    <span>{isIngesting ? "INGESTING..." : "RUN INGESTION"}</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
