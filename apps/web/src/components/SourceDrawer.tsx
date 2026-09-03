import React from "react";
import { EvidencePassage } from "@/lib/types";
import { X, ExternalLink, ShieldCheck, Clock, FileText, Globe } from "lucide-react";

interface SourceDrawerProps {
  passage: EvidencePassage | null;
  onClose: () => void;
}

export const SourceDrawer: React.FC<SourceDrawerProps> = ({ passage, onClose }) => {
  if (!passage) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-black/70 backdrop-blur-sm flex justify-end">
      <div className="w-full max-w-2xl bg-[#12161f] border-l border-[#232838] h-full flex flex-col shadow-2xl font-mono text-[#eceff3] animate-in slide-in-from-right duration-200">
        {/* Header */}
        <div className="p-4 border-b border-[#232838] flex items-center justify-between bg-[#171c27]">
          <div className="flex items-center space-x-2 text-xs">
            <ShieldCheck className="w-4 h-4 text-[#ffb627]" />
            <span className="text-[#ffb627] font-semibold tracking-wider uppercase">
              EVIDENCE PASSAGE INSPECTOR
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-[#8891a3] hover:text-white hover:bg-[#232838] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Metadata Block */}
          <div className="bg-[#0a0d12] border border-[#232838] p-4 rounded-lg space-y-3 text-xs">
            <div className="text-sm font-bold text-[#eceff3] font-sans">{passage.title}</div>
            
            <div className="grid grid-cols-2 gap-3 text-[#8891a3] pt-2 border-t border-[#232838]">
              <div className="flex items-center space-x-2">
                <Globe className="w-3.5 h-3.5 text-[#4ce0c6]" />
                <span>Publisher: <b className="text-[#eceff3]">{passage.publisher}</b></span>
              </div>
              <div className="flex items-center space-x-2">
                <Clock className="w-3.5 h-3.5 text-[#4ce0c6]" />
                <span>Published: <b className="text-[#eceff3]">{passage.published_at || "2026"}</b></span>
              </div>
            </div>

            <div className="flex items-center space-x-2 text-[#8891a3] pt-1">
              <FileText className="w-3.5 h-3.5 text-[#ffb627]" />
              <span className="truncate">URL / Path: <a href={passage.source_url} target="_blank" rel="noreferrer" className="text-[#4ce0c6] underline">{passage.source_url}</a></span>
            </div>
          </div>

          {/* Scores & Relevance Bar */}
          <div className="flex items-center justify-between bg-[#171c27] border border-[#8a6a2a] p-3.5 rounded-lg text-xs">
            <div>
              <span className="text-[#8891a3]">CONFIDENCE SCORE: </span>
              <span className="text-[#ffb627] font-bold text-sm">{(passage.confidence_score * 100).toFixed(0)}%</span>
            </div>
            <div>
              <span className="text-[#8891a3]">RELEVANCE MATRIX: </span>
              <span className="text-[#4ce0c6] font-bold">{passage.relevance_score.toFixed(3)}</span>
            </div>
          </div>

          {/* Passage Text Block */}
          <div>
            <div className="text-xs text-[#8891a3] uppercase tracking-wider mb-2 font-semibold flex items-center gap-2">
              <span className="w-1.5 h-1.5 bg-[#4ce0c6] rounded-full" />
              VERIFIED RELEVANT PASSAGE
            </div>
            <div className="bg-[#0a0d12] border border-[#232838] p-4 rounded-lg text-xs leading-relaxed text-[#eceff3] font-mono whitespace-pre-wrap selection:bg-[#ffb627] selection:text-[#0a0d12]">
              "{passage.text}"
            </div>
          </div>

          {/* Why Relevant Explanation */}
          <div className="bg-[#171c27]/60 border border-[#232838] p-4 rounded-lg text-xs space-y-1">
            <div className="text-[#ffb627] font-semibold">WHY THIS SOURCE MATTERS:</div>
            <div className="text-[#8891a3]">{passage.why_relevant}</div>
          </div>

          {/* Provenance Footer */}
          <div className="text-[10px] text-[#8891a3] border-t border-[#232838] pt-4 font-mono space-y-1">
            <div>PROVENANCE ID: <span className="text-[#eceff3]">{passage.passage_id}</span></div>
            <div>CHUNK ID: <span className="text-[#eceff3]">{passage.chunk_id}</span></div>
            <div>DOCUMENT ID: <span className="text-[#eceff3]">{passage.document_id}</span></div>
          </div>
        </div>

        {/* Footer Action */}
        <div className="p-4 border-t border-[#232838] bg-[#171c27] flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-[#232838] hover:bg-[#8a6a2a] text-[#eceff3] hover:text-[#0a0d12] font-semibold rounded text-xs transition-colors"
          >
            CLOSE INSPECTOR
          </button>
        </div>
      </div>
    </div>
  );
};
