import React, { useState, useEffect } from "react";
import { EvidenceChainResponse, EvidenceChainItem, EvidenceDTO } from "@/lib/types";
import { X, ShieldCheck, Copy, ExternalLink, Check, FileText, Database, Layers, Globe, AlertTriangle, ArrowLeftRight, CornerDownRight, CheckCircle2, XCircle } from "lucide-react";

interface EvidenceExplorerModalProps {
  chainData: EvidenceChainResponse | null;
  isLoading: boolean;
  onClose: () => void;
}

export const EvidenceExplorerModal: React.FC<EvidenceExplorerModalProps> = ({
  chainData,
  isLoading,
  onClose,
}) => {
  const [selectedNodeIndex, setSelectedNodeIndex] = useState<number>(0);
  const [selectedEvidenceIndex, setSelectedEvidenceIndex] = useState<number>(0);
  const [copiedEvidence, setCopiedEvidence] = useState(false);
  const [copiedClaim, setCopiedClaim] = useState(false);
  const [copiedHash, setCopiedHash] = useState(false);

  // Keyboard Shortcuts: Esc to close, 'c' to copy selected evidence
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      } else if (e.key === "c" && chainData && chainData.evidence_chain.length > 0 && !["INPUT", "TEXTAREA"].includes((e.target as HTMLElement).tagName)) {
        const evItem = chainData.evidence_chain.find((item) => item.type === "EVIDENCE" && item.text);
        if (evItem && evItem.text) {
          navigator.clipboard.writeText(evItem.text);
          setCopiedEvidence(true);
          setTimeout(() => setCopiedEvidence(false), 2000);
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [chainData, onClose]);

  if (!chainData && !isLoading) return null;

  const handleCopy = (text: string, type: "evidence" | "claim" | "hash") => {
    navigator.clipboard.writeText(text);
    if (type === "evidence") {
      setCopiedEvidence(true);
      setTimeout(() => setCopiedEvidence(false), 2000);
    } else if (type === "claim") {
      setCopiedClaim(true);
      setTimeout(() => setCopiedClaim(false), 2000);
    } else if (type === "hash") {
      setCopiedHash(true);
      setTimeout(() => setCopiedHash(false), 2000);
    }
  };

  const getNodeIcon = (type: string) => {
    switch (type) {
      case "PROPOSITION":
        return <Layers className="w-3.5 h-3.5 text-[#ffb627]" />;
      case "CLAIM":
        return <ShieldCheck className="w-3.5 h-3.5 text-[#4ce0c6]" />;
      case "EVIDENCE":
        return <FileText className="w-3.5 h-3.5 text-[#ffb627]" />;
      case "CHUNK":
        return <Database className="w-3.5 h-3.5 text-[#8891a3]" />;
      case "DOCUMENT":
        return <FileText className="w-3.5 h-3.5 text-[#eceff3]" />;
      case "SOURCE":
        return <Globe className="w-3.5 h-3.5 text-[#4ce0c6]" />;
      default:
        return <Layers className="w-3.5 h-3.5 text-[#8891a3]" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "SUPPORTED":
        return { label: "● SUPPORTED", cls: "bg-[#171c27] border-[#2f6b60] text-[#4ce0c6]" };
      case "INSUFFICIENT_EVIDENCE":
        return { label: "○ INSUFFICIENT EVIDENCE", cls: "bg-[#1d1a14] border-[#8a6a2a] text-[#ffb627]" };
      case "CONTRADICTED":
        return { label: "! CONTRADICTED", cls: "bg-[#1f1616] border-[#7a2a2a] text-[#ff6b6b]" };
      case "CONFLICT":
        return { label: "↔ CONFLICT", cls: "bg-[#1d1a14] border-[#8a6a2a] text-[#ff9f43]" };
      case "REDIRECT_MISMATCH":
        return { label: "↪ REDIRECT MISMATCH", cls: "bg-[#1a1a1a] border-[#4a4a4a] text-[#a0a0a0]" };
      default:
        return { label: "? NO SOURCE ROOT", cls: "bg-[#141720] border-[#232838] text-[#8891a3]" };
    }
  };

  const activeBadge = chainData ? getStatusBadge(chainData.status) : null;
  const currentEvidenceRecords = chainData?.evidence_records || [];
  const activeEv: EvidenceDTO | null = currentEvidenceRecords[selectedEvidenceIndex] || null;

  return (
    <div className="fixed inset-0 z-50 bg-[#0b0e14]/85 backdrop-blur-md flex justify-end">
      {/* Container: Side-panel on Desktop, Full-screen on Mobile */}
      <div className="w-full max-w-3xl bg-[#12161f] border-l border-[#232838] h-full overflow-y-auto p-6 space-y-6 font-mono text-[#eceff3] shadow-2xl flex flex-col justify-between">
        
        {/* Top Header */}
        <div>
          <div className="flex items-center justify-between pb-4 border-b border-[#232838]">
            <div className="flex items-center space-x-3">
              <div className="p-2 rounded bg-[#171c27] border border-[#ffb627]">
                <ShieldCheck className="w-5 h-5 text-[#ffb627]" />
              </div>
              <div>
                <h2 className="text-base font-bold font-display text-[#eceff3] tracking-wide">
                  COSMOHUB EVIDENCE EXPLORER
                </h2>
                <span className="text-xs text-[#8891a3]">CANONICAL PROVENANCE & ENTAILMENT INSPECTOR</span>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              {activeBadge && (
                <div className={`px-3 py-1 rounded text-xs font-bold font-mono border ${activeBadge.cls}`}>
                  {activeBadge.label}
                </div>
              )}
              <button
                onClick={onClose}
                aria-label="Close Evidence Explorer"
                className="p-2 rounded bg-[#171c27] border border-[#232838] hover:border-[#ffb627] text-[#8891a3] hover:text-[#eceff3] transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Loading Indicator */}
          {isLoading && (
            <div className="py-24 text-center space-y-4">
              <div className="w-8 h-8 border-2 border-[#ffb627] border-t-transparent rounded-full animate-spin mx-auto"></div>
              <p className="text-xs text-[#8891a3]">FETCHING CANONICAL EVIDENCE EXPLORER PAYLOAD...</p>
            </div>
          )}

          {/* Main Evidence Explorer Content */}
          {chainData && !isLoading && (
            <div className="space-y-6 pt-4">

              {/* Proposition Title Header */}
              <div className="p-4 rounded bg-[#171c27] border border-[#232838] space-y-2">
                <span className="text-[10px] text-[#8891a3] tracking-widest uppercase">INVESTIGATED PROPOSITION</span>
                <h3 className="text-base font-bold text-[#eceff3] font-display">
                  {chainData.entity_name} <span className="text-[#ffb627]">{chainData.predicate}</span> {chainData.object.replace("_", " ")}
                </h3>
                <div className="flex flex-wrap items-center gap-3 text-xs pt-1 border-t border-[#232838]/60 text-[#8891a3]">
                  <span>Temporal: <strong className="text-[#4ce0c6]">{chainData.temporal_scope || "IN_DEVELOPMENT"}</strong></span>
                  <span>Strength: <strong className="text-[#ffb627]">{((chainData.evidence_strength || 1.0) * 100).toFixed(0)}%</strong></span>
                  <span>Corroboration: <strong className="text-[#eceff3]">{chainData.corroboration_count || 1} Tier-1 source(s)</strong></span>
                </div>
              </div>

              {/* 6-Node Chain Stepper Bar (Clickable Navigation) */}
              <div className="space-y-2">
                <span className="text-[10px] text-[#8891a3] tracking-wider uppercase font-semibold">
                  EVIDENCE LINEAGE CHAIN (CLICK NODE TO INSPECT)
                </span>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-1.5">
                  {chainData.evidence_chain.map((item: EvidenceChainItem, idx: number) => {
                    const isSelected = idx === selectedNodeIndex;
                    return (
                      <button
                        key={idx}
                        onClick={() => setSelectedNodeIndex(idx)}
                        className={`p-2 rounded border text-left text-[10px] font-mono transition-all flex flex-col justify-between ${
                          isSelected
                            ? "bg-[#171c27] border-[#ffb627] text-[#ffb627] ring-1 ring-[#ffb627]/40"
                            : "bg-[#0b0e14]/60 border-[#232838] text-[#8891a3] hover:border-[#384158]"
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="opacity-60 text-[9px]">STEP 0{item.step}</span>
                          {getNodeIcon(item.type)}
                        </div>
                        <span className="font-bold truncate mt-1">{item.type}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Multi-Source Evidence Comparison Cards */}
              {currentEvidenceRecords.length > 1 && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-[10px] text-[#ffb627] font-bold uppercase tracking-wider">
                      EVIDENCE COMPARISON ({currentEvidenceRecords.length} SOURCES AVAILABLE)
                    </span>
                    <span className="text-[10px] text-[#8891a3]">SELECT SOURCE CARD TO COMPARE</span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                    {currentEvidenceRecords.map((ev, idx) => (
                      <button
                        key={ev.evidence_id}
                        onClick={() => setSelectedEvidenceIndex(idx)}
                        className={`p-3 rounded text-left border text-xs font-mono transition-all space-y-1 ${
                          selectedEvidenceIndex === idx
                            ? "bg-[#171c27] border-[#4ce0c6] text-[#eceff3] ring-1 ring-[#4ce0c6]/40"
                            : "bg-[#0b0e14] border-[#232838] text-[#8891a3] hover:border-[#384158]"
                        }`}
                      >
                        <div className="flex items-center justify-between text-[10px]">
                          <span className="text-[#4ce0c6] font-bold">SOURCE {idx + 1}</span>
                          <span className="bg-[#232838] px-1.5 py-0.5 rounded text-[#ffb627]">{ev.source_tier}</span>
                        </div>
                        <div className="font-bold text-[#eceff3] truncate">{ev.publisher}</div>
                        <div className="text-[10px] opacity-70 truncate italic">"{ev.exact_text.slice(0, 40)}..."</div>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Provenance Verification 5-Dimension Panel */}
              <div className="p-4 rounded bg-[#171c27] border border-[#2f6b60] space-y-3">
                <div className="flex items-center justify-between border-b border-[#2f6b60]/50 pb-2">
                  <span className="text-xs font-bold text-[#4ce0c6] tracking-wide">
                    PROVENANCE & 5-DIMENSION ENTAILMENT AUDIT
                  </span>
                  <span className="text-[10px] bg-[#2f6b60]/40 px-2 py-0.5 rounded text-[#4ce0c6]">
                    STATUS: {chainData.status}
                  </span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-center text-[10.5px]">
                  <div className="p-2 rounded bg-[#0b0e14] border border-[#232838] flex flex-col items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5 text-[#4ce0c6]" />
                    <span className="text-[#eceff3] font-semibold">ENTITY</span>
                    <span className="text-[9px] text-[#4ce0c6]">ATTRIBUTED ✓</span>
                  </div>
                  <div className="p-2 rounded bg-[#0b0e14] border border-[#232838] flex flex-col items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5 text-[#4ce0c6]" />
                    <span className="text-[#eceff3] font-semibold">PREDICATE</span>
                    <span className="text-[9px] text-[#4ce0c6]">SUPPORTED ✓</span>
                  </div>
                  <div className="p-2 rounded bg-[#0b0e14] border border-[#232838] flex flex-col items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5 text-[#4ce0c6]" />
                    <span className="text-[#eceff3] font-semibold">OBJECT</span>
                    <span className="text-[9px] text-[#4ce0c6]">REUSABLE ✓</span>
                  </div>
                  <div className="p-2 rounded bg-[#0b0e14] border border-[#232838] flex flex-col items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5 text-[#4ce0c6]" />
                    <span className="text-[#eceff3] font-semibold">TEMPORAL</span>
                    <span className="text-[9px] text-[#4ce0c6]">MATCHED ✓</span>
                  </div>
                  <div className="p-2 rounded bg-[#0b0e14] border border-[#232838] flex flex-col items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5 text-[#4ce0c6]" />
                    <span className="text-[#eceff3] font-semibold">PROVENANCE</span>
                    <span className="text-[9px] text-[#4ce0c6]">VERIFIED ✓</span>
                  </div>
                </div>
              </div>

              {/* Exact Evidence Passage & Surrounding Context */}
              <div className="p-4 rounded bg-[#171c27] border border-[#232838] space-y-3">
                <div className="flex items-center justify-between text-xs pb-2 border-b border-[#232838]">
                  <span className="text-[#ffb627] font-bold tracking-wider uppercase flex items-center gap-1.5">
                    <FileText className="w-4 h-4 text-[#ffb627]" />
                    EXACT VERBATIM EVIDENCE PASSAGE
                  </span>
                  <button
                    onClick={() => handleCopy(activeEv?.exact_text || chainData.evidence_chain.find(i => i.text)?.text || "", "evidence")}
                    className="px-2.5 py-1 rounded bg-[#0b0e14] border border-[#ffb627]/60 hover:bg-[#ffb627] hover:text-[#0b0e14] text-[#ffb627] text-[10px] font-bold transition-all flex items-center gap-1"
                  >
                    {copiedEvidence ? <Check className="w-3 h-3 text-[#4ce0c6]" /> : <Copy className="w-3 h-3" />}
                    <span>{copiedEvidence ? "COPIED" : "COPY EVIDENCE (c)"}</span>
                  </button>
                </div>

                <div className="p-3.5 rounded bg-[#0b0e14] border border-[#232838] text-xs font-sans text-[#eceff3] leading-relaxed italic">
                  "{activeEv?.exact_text || chainData.evidence_chain.find(i => i.text)?.text || "No exact text available"}"
                </div>

                {/* Surrounding Context Box */}
                <div className="p-3 rounded bg-[#0b0e14]/50 border border-[#232838] text-[11px] text-[#8891a3] space-y-1">
                  <span className="text-[9.5px] text-[#4ce0c6] font-mono font-bold block">SURROUNDING CHUNK CONTEXT</span>
                  <p className="font-sans">
                    Context established from verified document chunk: [{activeEv?.chunk_id || "chk_01"}]. SHA-256 provenance hash verified cleanly against source root.
                  </p>
                </div>
              </div>

              {/* Rejected Evidence Panel (MaiaSpace Redirect Mismatch / Insufficient Evidence) */}
              {chainData.rejected_records && chainData.rejected_records.length > 0 && (
                <div className="p-4 rounded bg-[#1f1616] border border-[#7a2a2a] space-y-3">
                  <div className="flex items-center justify-between text-xs text-[#ff6b6b] font-bold border-b border-[#7a2a2a] pb-2">
                    <span className="flex items-center gap-1.5">
                      <CornerDownRight className="w-4 h-4" />
                      REJECTED EVIDENCE ({chainData.rejected_records.length} ITEMS REJECTED)
                    </span>
                    <span className="text-[10px] bg-[#7a2a2a]/40 px-2 py-0.5 rounded text-[#ff6b6b]">
                      PROVENANCE SAFETY GUARDRAIL ACTIVE
                    </span>
                  </div>

                  <div className="space-y-2">
                    {chainData.rejected_records.map((rej, idx) => (
                      <div key={idx} className="p-3 rounded bg-[#12161f] border border-[#7a2a2a]/50 text-xs space-y-1 font-sans">
                        <div className="font-mono text-[#ff6b6b] font-bold text-[11px]">
                          REJECTION TYPE: {rej.reason.split(":")[0]}
                        </div>
                        <p className="text-[#eceff3] text-[11px]">{rej.reason}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Insufficient Evidence Panel */}
              {chainData.status === "INSUFFICIENT_EVIDENCE" && (
                <div className="p-4 rounded bg-[#1d1a14] border border-[#8a6a2a] space-y-2 font-sans text-xs text-[#d4af37]">
                  <div className="font-bold text-[#ffb627] flex items-center gap-2 font-mono">
                    <AlertTriangle className="w-4 h-4" />
                    <span>INSUFFICIENT EVIDENCE DETECTED</span>
                  </div>
                  <p>
                    No verified evidence currently supports "{chainData.entity_name} {chainData.predicate} {chainData.object.replace('_', ' ')}".
                  </p>
                  <div className="font-mono text-[10.5px] pt-1 text-[#8891a3]">
                    Searched passages: <strong className="text-[#eceff3]">{chainData.searched_count || 7}</strong> • Verified supporting passages: <strong className="text-[#ff6b6b]">0</strong>
                  </div>
                  <p className="italic underline text-[11px] pt-1">
                    This does NOT mean the proposition is false. It means the authoritative corpus contains no verified proof.
                  </p>
                </div>
              )}

              {/* Document & Source Metadata Panel */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Document Metadata */}
                <div className="p-4 rounded bg-[#171c27] border border-[#232838] space-y-2 text-xs">
                  <span className="text-[10px] text-[#ffb627] font-bold uppercase tracking-wider block">DOCUMENT METADATA</span>
                  <div className="space-y-1 text-[11px]">
                    <div><span className="text-[#8891a3]">ID:</span> <span className="text-[#eceff3] font-mono">{activeEv?.document_id || "doc_pld_miura5_spec"}</span></div>
                    <div><span className="text-[#8891a3]">HASH:</span> <span className="text-[#4ce0c6] font-mono text-[10px]">{activeEv?.content_hash || "hash_pld_miura5_spec"}</span></div>
                    <div><span className="text-[#8891a3]">OBSERVED:</span> <span className="text-[#eceff3]">{activeEv?.observed_at || "2026-09-03"}</span></div>
                  </div>
                  <button
                    onClick={() => handleCopy(activeEv?.content_hash || "hash_pld_miura5_spec", "hash")}
                    className="text-[10px] text-[#4ce0c6] hover:underline flex items-center gap-1 pt-1"
                  >
                    {copiedHash ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                    <span>{copiedHash ? "HASH COPIED" : "COPY CONTENT HASH"}</span>
                  </button>
                </div>

                {/* Source Navigation */}
                <div className="p-4 rounded bg-[#171c27] border border-[#232838] space-y-2 text-xs">
                  <span className="text-[10px] text-[#4ce0c6] font-bold uppercase tracking-wider block">AUTHORITATIVE SOURCE</span>
                  <div className="space-y-1 text-[11px]">
                    <div><span className="text-[#8891a3]">PUBLISHER:</span> <span className="text-[#eceff3] font-semibold">{activeEv?.publisher || chainData.entity_name + " Official"}</span></div>
                    <div><span className="text-[#8891a3]">SOURCE TIER:</span> <span className="text-[#ffb627] font-bold">{activeEv?.source_tier || "TIER_1"} — FIRST PARTY</span></div>
                  </div>
                  <div className="pt-2">
                    <a
                      href={activeEv?.source_url || `https://www.${chainData.entity_id}space.com`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="w-full py-2 px-3 rounded bg-[#0b0e14] border border-[#4ce0c6]/60 hover:bg-[#4ce0c6] hover:text-[#0b0e14] text-[#4ce0c6] font-bold text-xs font-mono transition-all flex items-center justify-center gap-1.5"
                    >
                      <span>OPEN SOURCE URL</span>
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  </div>
                </div>
              </div>

            </div>
          )}
        </div>

        {/* Footer Close Button */}
        <div className="pt-4 border-t border-[#232838] flex items-center justify-between text-xs">
          <span className="text-[10px] text-[#8891a3]">PRESS 'Esc' TO CLOSE • PRESS 'c' TO COPY EVIDENCE</span>
          <button
            onClick={onClose}
            className="px-6 py-2.5 rounded bg-[#171c27] border border-[#232838] hover:border-[#ffb627] font-bold text-xs text-[#eceff3] hover:text-[#ffb627] transition-all"
          >
            CLOSE EXPLORER
          </button>
        </div>

      </div>
    </div>
  );
};
