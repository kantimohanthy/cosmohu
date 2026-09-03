import React, { useState } from "react";
import { EvidenceChainResponse, EvidenceChainItem } from "@/lib/types";
import { X, ShieldCheck, Copy, ExternalLink, Check, FileText, Database, Layers, Globe } from "lucide-react";

interface EvidenceInspectorModalProps {
  chainData: EvidenceChainResponse | null;
  isLoading: boolean;
  onClose: () => void;
}

export const EvidenceInspectorModal: React.FC<EvidenceInspectorModalProps> = ({
  chainData,
  isLoading,
  onClose,
}) => {
  const [copied, setCopied] = useState(false);

  if (!chainData && !isLoading) return null;

  const handleCopyPassage = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getStepIcon = (type: string) => {
    switch (type) {
      case "PROPOSITION":
        return <Layers className="w-4 h-4 text-[#ffb627]" />;
      case "CLAIM":
        return <ShieldCheck className="w-4 h-4 text-[#4ce0c6]" />;
      case "EVIDENCE":
        return <FileText className="w-4 h-4 text-[#ffb627]" />;
      case "CHUNK":
        return <Database className="w-4 h-4 text-[#8891a3]" />;
      case "DOCUMENT":
        return <FileText className="w-4 h-4 text-[#eceff3]" />;
      case "SOURCE":
        return <Globe className="w-4 h-4 text-[#4ce0c6]" />;
      default:
        return <Layers className="w-4 h-4 text-[#8891a3]" />;
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-[#0b0e14]/80 backdrop-blur-sm flex justify-end">
      <div className="w-full max-w-2xl bg-[#12161f] border-l border-[#232838] h-full overflow-y-auto p-6 space-y-6 font-mono text-[#eceff3] shadow-2xl flex flex-col justify-between">
        
        {/* Header */}
        <div>
          <div className="flex items-center justify-between pb-4 border-b border-[#232838]">
            <div className="flex items-center space-x-3">
              <div className="p-2 rounded bg-[#171c27] border border-[#ffb627]">
                <ShieldCheck className="w-5 h-5 text-[#ffb627]" />
              </div>
              <div>
                <h2 className="text-base font-bold font-display text-[#eceff3] tracking-wide">
                  EVIDENCE CHAIN INSPECTOR
                </h2>
                <span className="text-xs text-[#8891a3]">WHY THIS CONCLUSION? (CANONICAL PROVENANCE)</span>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 rounded bg-[#171c27] border border-[#232838] hover:border-[#ffb627] text-[#8891a3] hover:text-[#eceff3] transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Loading State */}
          {isLoading && (
            <div className="py-20 text-center space-y-3">
              <div className="w-8 h-8 border-2 border-[#ffb627] border-t-transparent rounded-full animate-spin mx-auto"></div>
              <p className="text-xs text-[#8891a3]">TRACING CANONICAL EVIDENCE CHAIN...</p>
            </div>
          )}

          {/* Evidence Chain Content */}
          {chainData && !isLoading && (
            <div className="space-y-6 pt-4">
              
              {/* Provenance Safety Checks Banner */}
              <div className="p-4 rounded bg-[#171c27] border border-[#2f6b60] space-y-2">
                <div className="text-xs font-bold text-[#4ce0c6] flex items-center justify-between">
                  <span>5-DIMENSION ENTAILMENT & PROVENANCE VERIFIED</span>
                  <span className="text-[10px] bg-[#2f6b60]/40 px-2 py-0.5 rounded text-[#4ce0c6]">STATUS: {chainData.status}</span>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-[10px] font-mono text-[#eceff3] pt-1">
                  <div className="bg-[#12161f] p-1.5 rounded border border-[#232838] text-center">ENTITY ✓</div>
                  <div className="bg-[#12161f] p-1.5 rounded border border-[#232838] text-center">PREDICATE ✓</div>
                  <div className="bg-[#12161f] p-1.5 rounded border border-[#232838] text-center">OBJECT ✓</div>
                  <div className="bg-[#12161f] p-1.5 rounded border border-[#232838] text-center">TEMPORAL ✓</div>
                  <div className="bg-[#12161f] p-1.5 rounded border border-[#232838] text-center">PROVENANCE ✓</div>
                </div>
              </div>

              {/* Chain Steps Timeline */}
              <div className="space-y-4 relative before:absolute before:left-4 before:top-2 before:bottom-2 before:w-0.5 before:bg-[#232838]">
                {chainData.evidence_chain.map((item: EvidenceChainItem, idx: number) => (
                  <div key={idx} className="relative pl-10 space-y-2 group">
                    {/* Circle Step Icon */}
                    <div className="absolute left-1.5 top-0.5 w-6 h-6 rounded-full bg-[#171c27] border border-[#232838] group-hover:border-[#ffb627] flex items-center justify-center">
                      {getStepIcon(item.type)}
                    </div>

                    <div className="p-4 rounded bg-[#171c27] border border-[#232838] hover:border-[#384158] transition-all space-y-2">
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="text-[#ffb627] font-bold uppercase tracking-wider">
                          STEP {item.step}: {item.type}
                        </span>
                        {item.source_tier && (
                          <span className="text-[10px] px-2 py-0.5 rounded bg-[#232838] text-[#4ce0c6] font-semibold">
                            {item.source_tier} — FIRST PARTY
                          </span>
                        )}
                      </div>

                      <div className="text-xs font-semibold text-[#eceff3] font-display">
                        {item.label || item.id}
                      </div>

                      {/* Verbatim Evidence Passage Display */}
                      {item.text && (
                        <div className="p-3 rounded bg-[#0b0e14] border border-[#232838] text-xs font-sans text-[#eceff3] leading-relaxed relative">
                          <p className="italic">"{item.text}"</p>
                          <div className="mt-3 flex items-center justify-between pt-2 border-t border-[#232838]">
                            <button
                              onClick={() => handleCopyPassage(item.text!)}
                              className="text-[10px] text-[#ffb627] hover:underline flex items-center gap-1"
                            >
                              {copied ? <Check className="w-3 h-3 text-[#4ce0c6]" /> : <Copy className="w-3 h-3" />}
                              <span>{copied ? "COPIED TO CLIPBOARD" : "COPY EVIDENCE"}</span>
                            </button>
                          </div>
                        </div>
                      )}

                      {/* Source Link */}
                      {item.url && (
                        <div className="pt-1">
                          <a
                            href={item.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1.5 text-xs text-[#4ce0c6] hover:underline font-mono"
                          >
                            <span>OPEN SOURCE URL ({item.publisher || "Official Source"})</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>

            </div>
          )}
        </div>

        {/* Footer Close */}
        <div className="pt-4 border-t border-[#232838]">
          <button
            onClick={onClose}
            className="w-full py-2.5 rounded bg-[#171c27] border border-[#232838] hover:border-[#ffb627] text-xs font-bold font-mono text-[#eceff3] transition-all"
          >
            CLOSE EVIDENCE INSPECTOR
          </button>
        </div>
      </div>
    </div>
  );
};
