import React from "react";
import { ResearchQueryResponse } from "@/lib/types";
import { Clock, Cpu, Database, CheckCircle, AlertCircle } from "lucide-react";

interface ResearchMetadataPanelProps {
  data: ResearchQueryResponse;
}

export const ResearchMetadataPanel: React.FC<ResearchMetadataPanelProps> = ({ data }) => {
  const meta = data.metadata || {};
  const supportedCount = data.propositions.filter((p) => p.status === "SUPPORTED").length;
  const insufficientCount = data.propositions.filter((p) => p.status === "INSUFFICIENT_EVIDENCE").length;
  const conflictCount = data.conflicts.length;

  return (
    <div className="p-4 rounded-lg bg-[#12161f] border border-[#232838] font-mono text-xs text-[#eceff3] space-y-3 shadow-md">
      <div className="flex items-center justify-between pb-2 border-b border-[#232838]">
        <div className="flex items-center space-x-2 text-[#ffb627] font-bold">
          <Cpu className="w-4 h-4" />
          <span>RESEARCH ENGINE METADATA</span>
        </div>
        <div className="text-[10px] text-[#4ce0c6] bg-[#171c27] px-2 py-0.5 rounded border border-[#2f6b60]">
          PROVIDER: {meta.provider_type || "DETERMINISTIC FALLBACK"}
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-center">
        <div className="bg-[#171c27] p-2 rounded border border-[#232838]">
          <span className="text-[10px] text-[#8891a3] block">PROPOSITIONS</span>
          <span className="text-sm font-bold text-[#eceff3]">{data.propositions.length}</span>
        </div>
        <div className="bg-[#171c27] p-2 rounded border border-[#232838]">
          <span className="text-[10px] text-[#8891a3] block">SUPPORTED</span>
          <span className="text-sm font-bold text-[#4ce0c6]">{supportedCount}</span>
        </div>
        <div className="bg-[#171c27] p-2 rounded border border-[#232838]">
          <span className="text-[10px] text-[#8891a3] block">INSUFFICIENT</span>
          <span className="text-sm font-bold text-[#ffb627]">{insufficientCount}</span>
        </div>
        <div className="bg-[#171c27] p-2 rounded border border-[#232838]">
          <span className="text-[10px] text-[#8891a3] block">EVIDENCE ITEMS</span>
          <span className="text-sm font-bold text-[#eceff3]">{data.evidence.length}</span>
        </div>
        <div className="bg-[#171c27] p-2 rounded border border-[#232838]">
          <span className="text-[10px] text-[#8891a3] block">TOTAL LATENCY</span>
          <span className="text-sm font-bold text-[#ffb627]">{meta.total_ms || 18.0} ms</span>
        </div>
      </div>

      {/* Latency Breakdown Line */}
      <div className="pt-2 text-[10px] text-[#8891a3] flex flex-wrap items-center justify-between border-t border-[#232838] gap-2">
        <span>Planning: {meta.planning_ms || 0}ms</span>
        <span>Retrieval: {meta.retrieval_ms || 0}ms</span>
        <span>Reranking: {meta.reranking_ms || 0}ms</span>
        <span>Verification: {meta.verification_ms || 0}ms</span>
        <span>Validation: {meta.validation_ms || 0}ms</span>
      </div>
    </div>
  );
};
