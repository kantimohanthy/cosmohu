import React from "react";
import { PropositionDTO } from "@/lib/types";
import { ShieldCheck, AlertCircle, ArrowLeftRight, HelpCircle, CornerDownRight, FileSearch } from "lucide-react";

interface PropositionCardProps {
  proposition: PropositionDTO;
  onInspectEvidenceChain: (propositionId: string) => void;
}

export const PropositionCard: React.FC<PropositionCardProps> = ({
  proposition,
  onInspectEvidenceChain,
}) => {
  const getStatusBadge = (status: string) => {
    switch (status) {
      case "SUPPORTED":
        return {
          icon: <ShieldCheck className="w-4 h-4 text-[#4ce0c6]" />,
          label: "● SUPPORTED",
          cls: "bg-[#171c27] border-[#2f6b60] text-[#4ce0c6]"
        };
      case "INSUFFICIENT_EVIDENCE":
        return {
          icon: <AlertCircle className="w-4 h-4 text-[#ffb627]" />,
          label: "○ INSUFFICIENT EVIDENCE",
          cls: "bg-[#1d1a14] border-[#8a6a2a] text-[#ffb627]"
        };
      case "CONTRADICTED":
        return {
          icon: <AlertCircle className="w-4 h-4 text-[#ff6b6b]" />,
          label: "! CONTRADICTED",
          cls: "bg-[#1f1616] border-[#7a2a2a] text-[#ff6b6b]"
        };
      case "CONFLICT":
        return {
          icon: <ArrowLeftRight className="w-4 h-4 text-[#ff9f43]" />,
          label: "↔ CONFLICT",
          cls: "bg-[#1d1a14] border-[#8a6a2a] text-[#ff9f43]"
        };
      case "REDIRECT_MISMATCH":
        return {
          icon: <CornerDownRight className="w-4 h-4 text-[#a0a0a0]" />,
          label: "↪ REDIRECT MISMATCH",
          cls: "bg-[#1a1a1a] border-[#4a4a4a] text-[#a0a0a0]"
        };
      default:
        return {
          icon: <HelpCircle className="w-4 h-4 text-[#8891a3]" />,
          label: "? NO SOURCE ROOT",
          cls: "bg-[#141720] border-[#232838] text-[#8891a3]"
        };
    }
  };

  const badge = getStatusBadge(proposition.status);

  return (
    <div className="p-5 rounded-lg bg-[#12161f] border border-[#232838] hover:border-[#384158] transition-all font-mono space-y-4 shadow-md">
      {/* Card Header & Status */}
      <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-[#232838]">
        <div>
          <span className="text-[10px] text-[#8891a3] tracking-widest uppercase">ENTITY INVESTIGATED</span>
          <h3 className="text-base font-bold text-[#eceff3] font-display">{proposition.entity_name}</h3>
        </div>
        <div className={`px-3 py-1 rounded text-xs font-bold font-mono border flex items-center gap-1.5 ${badge.cls}`}>
          {badge.icon}
          <span>{badge.label}</span>
        </div>
      </div>

      {/* Factual Statement / Description */}
      <div className="space-y-2 text-xs">
        {proposition.status === "SUPPORTED" ? (
          <div className="p-3 rounded bg-[#171c27] border border-[#2f6b60]/50 text-[#eceff3] font-sans">
            <span className="font-bold text-[#4ce0c6]">{proposition.entity_name}</span> is verified to be <span className="font-semibold">{proposition.predicate}</span> <span className="text-[#ffb627]">{proposition.object.replace("_", " ")}</span>.
          </div>
        ) : proposition.status === "INSUFFICIENT_EVIDENCE" ? (
          <div className="p-3 rounded bg-[#1d1a14] border border-[#8a6a2a]/50 text-[#d4af37] font-sans">
            The current evidence corpus does not provide sufficient verified evidence for this proposition. <span className="underline italic">This does NOT mean the proposition is false.</span>
          </div>
        ) : (
          <div className="p-3 rounded bg-[#1f1616] border border-[#7a2a2a]/50 text-[#ff6b6b] font-sans">
            Status: {proposition.status}. No verified positive claim supported.
          </div>
        )}
      </div>

      {/* Proposition Metadata Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] bg-[#171c27] p-3 rounded border border-[#232838]">
        <div>
          <span className="text-[#8891a3] block text-[9.5px]">TEMPORAL SCOPE</span>
          <span className="text-[#eceff3] font-semibold">{proposition.temporal_scope}</span>
        </div>
        <div>
          <span className="text-[#8891a3] block text-[9.5px]">EVIDENCE STRENGTH</span>
          <span className="text-[#ffb627] font-semibold">{(proposition.evidence_strength * 100).toFixed(0)}%</span>
        </div>
        <div>
          <span className="text-[#8891a3] block text-[9.5px]">EVIDENCE RECORDS</span>
          <span className="text-[#4ce0c6] font-semibold">{proposition.evidence_ids.length}</span>
        </div>
        <div>
          <span className="text-[#8891a3] block text-[9.5px]">PROPOSITION ID</span>
          <span className="text-[#eceff3] font-mono text-[10px] truncate block">{proposition.proposition_id}</span>
        </div>
      </div>

      {/* WHY THIS CONCLUSION Interaction Button */}
      <div className="pt-2">
        <button
          onClick={() => onInspectEvidenceChain(proposition.proposition_id)}
          className="w-full py-2.5 px-4 rounded bg-[#171c27] border border-[#ffb627]/60 hover:bg-[#ffb627] hover:text-[#0b0e14] text-[#ffb627] font-bold text-xs font-mono transition-all flex items-center justify-center gap-2 group"
        >
          <FileSearch className="w-4 h-4 group-hover:scale-110 transition-transform" />
          <span>WHY THIS CONCLUSION? (INSPECT EVIDENCE CHAIN)</span>
        </button>
      </div>
    </div>
  );
};
