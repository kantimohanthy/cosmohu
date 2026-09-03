"use client";

import React, { useState, useEffect } from "react";
import { QueryInput } from "@/components/QueryInput";
import { ProcessStepper } from "@/components/ProcessStepper";
import { PropositionCard } from "@/components/PropositionCard";
import { EvidenceExplorerModal } from "@/components/EvidenceExplorerModal";
import { ResearchMetadataPanel } from "@/components/ResearchMetadataPanel";
import { InvestigationSidebar } from "@/components/InvestigationSidebar";
import { EntityComparisonView } from "@/components/EntityComparisonView";
import { EvidenceGraphView } from "@/components/EvidenceGraphView";
import { ResearchEmptyState } from "@/components/ResearchEmptyState";
import { ResearchSession, EvidenceChainResponse, PropositionDTO } from "@/lib/types";
import {
  createResearchSession,
  fetchResearchSessions,
  fetchResearchSession,
  addQueryToResearchSession,
  deleteResearchSession,
  fetchWhyConclusionEvidenceChain
} from "@/lib/api";
import { Cpu, ShieldCheck, Sparkles, AlertTriangle, Copy, Check, BarChart2, Table, Network, Filter } from "lucide-react";

export default function ResearchHomePage() {
  const [sessionsList, setSessionsList] = useState<ResearchSession[]>([]);
  const [currentSession, setCurrentSession] = useState<ResearchSession | null>(null);
  const [queryValue, setQueryValue] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);
  const [activeStepIndex, setActiveStepIndex] = useState(0);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Active View Mode Tab: 'workspace' | 'comparison' | 'graph'
  const [viewMode, setViewMode] = useState<"workspace" | "comparison" | "graph">("workspace");

  // Proposition Filter: 'ALL' | 'SUPPORTED' | 'INSUFFICIENT_EVIDENCE' | 'CONTRADICTED' | 'CONFLICT' | 'REDIRECT_MISMATCH'
  const [propStatusFilter, setPropStatusFilter] = useState<string>("ALL");
  const [activeEntityFilter, setActiveEntityFilter] = useState<string | null>(null);

  // Evidence Explorer Modal State
  const [selectedChain, setSelectedChain] = useState<EvidenceChainResponse | null>(null);
  const [isChainLoading, setIsChainLoading] = useState(false);
  const [copiedSummary, setCopiedSummary] = useState(false);

  useEffect(() => {
    // Initial Sessions Load & URL Deep-Linking Recovery
    async function initSessions() {
      try {
        const list = await fetchResearchSessions();
        setSessionsList(list);

        if (typeof window !== "undefined") {
          const params = new URLSearchParams(window.location.search);
          const sParam = params.get("session");
          const propParam = params.get("proposition");

          if (sParam) {
            const found = await fetchResearchSession(sParam);
            setCurrentSession(found);
            if (propParam) {
              handleInspectEvidenceChain(propParam);
            }
            return;
          }
        }

        if (list.length > 0) {
          setCurrentSession(list[0]);
        } else {
          // Auto-create initial session if empty
          const newSess = await createResearchSession("European Launch Vehicle Intelligence");
          setCurrentSession(newSess);
          setSessionsList([newSess]);
        }
      } catch (err) {
        console.error("Session initialization error:", err);
      }
    }

    initSessions();
  }, []);

  const handleCreateNewSession = async () => {
    try {
      const newSess = await createResearchSession("New Space Intelligence Investigation");
      setCurrentSession(newSess);
      const list = await fetchResearchSessions();
      setSessionsList(list);
    } catch (err: any) {
      setErrorMsg(`Failed to create session: ${err.message}`);
    }
  };

  const handleSelectSession = async (sessionId: string) => {
    try {
      const sess = await fetchResearchSession(sessionId);
      setCurrentSession(sess);

      if (typeof window !== "undefined") {
        const url = new URL(window.location.href);
        url.searchParams.set("session", sessionId);
        window.history.pushState({}, "", url.toString());
      }
    } catch (err: any) {
      setErrorMsg(`Failed to load session: ${err.message}`);
    }
  };

  const handleDeleteSession = async (sessionId: string) => {
    try {
      await deleteResearchSession(sessionId);
      const list = await fetchResearchSessions();
      setSessionsList(list);
      if (list.length > 0) {
        setCurrentSession(list[0]);
      } else {
        const newSess = await createResearchSession("European Launch Vehicle Intelligence");
        setCurrentSession(newSess);
        setSessionsList([newSess]);
      }
    } catch (err: any) {
      setErrorMsg(`Failed to delete session: ${err.message}`);
    }
  };

  const handleExecuteResearch = async (queryText: string) => {
    setQueryValue(queryText);
    setIsLoading(true);
    setErrorMsg(null);
    setActiveStepIndex(0);

    let activeSessionId = currentSession?.session_id;
    if (!activeSessionId) {
      const newSess = await createResearchSession(queryText.slice(0, 50));
      activeSessionId = newSess.session_id;
    }

    const interval = setInterval(() => {
      setActiveStepIndex((prev) => (prev < 5 ? prev + 1 : prev));
    }, 180);

    try {
      const updatedSession = await addQueryToResearchSession(activeSessionId, queryText);
      clearInterval(interval);
      setActiveStepIndex(5);
      setCurrentSession(updatedSession);

      const list = await fetchResearchSessions();
      setSessionsList(list);
    } catch (err: any) {
      clearInterval(interval);
      setErrorMsg(`RESEARCH FAILED: ${err.message || "The intelligence service could not complete this query."}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleInspectEvidenceChain = async (propositionId: string) => {
    setIsChainLoading(true);
    setSelectedChain(null);

    if (typeof window !== "undefined") {
      const url = new URL(window.location.href);
      url.searchParams.set("proposition", propositionId);
      window.history.pushState({}, "", url.toString());
    }

    try {
      const chainData = await fetchWhyConclusionEvidenceChain(propositionId);
      setSelectedChain(chainData);
    } catch (err: any) {
      alert(`Evidence chain error: ${err.message}`);
    } finally {
      setIsChainLoading(false);
    }
  };

  const handleCopyResearchSummary = () => {
    if (!currentSession) return;
    const meta = currentSession.metadata;
    const summaryMd = `
# COSMOHUB RESEARCH SUMMARY
**Investigation**: ${currentSession.title}
**Session ID**: ${currentSession.session_id}
**Updated**: ${currentSession.updated_at}

## Key Metrics
- Total Queries: ${meta.total_queries}
- Discovered Entities: ${meta.total_entities}
- Verified Propositions: ${meta.supported_count} / ${meta.total_propositions}
- Evidence Density: ${meta.evidence_density}%
- Tier-1 Sources: ${meta.tier1_source_count}

## Verified Claims
${currentSession.supported_claims.map((c) => `- **[${c.verification_status}]** ${c.text}`).join("\n")}

## Insufficient Evidence Findings
${currentSession.insufficient_propositions.map((i) => `- **[INSUFFICIENT]** ${i.entity_name}: ${i.reason}`).join("\n")}

---
*Generated by CosmoHub Space Intelligence Engine V1*
`.trim();

    navigator.clipboard.writeText(summaryMd);
    setCopiedSummary(true);
    setTimeout(() => setCopiedSummary(false), 2000);
  };

  // Filter propositions based on status and entity filter
  const filteredPropositions = (currentSession?.propositions || []).filter((p) => {
    const matchesStatus = propStatusFilter === "ALL" || p.status === propStatusFilter;
    const matchesEntity = activeEntityFilter === null || p.entity_id === activeEntityFilter;
    return matchesStatus && matchesEntity;
  });

  return (
    <div className="min-h-screen bg-[#0b0e14] font-mono text-[#eceff3] pb-12">
      {/* Top Banner Bar */}
      <header className="border-b border-[#232838] bg-[#12161f] px-6 py-3 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-1.5 rounded bg-[#171c27] border border-[#ffb627]">
            <Cpu className="w-4 h-4 text-[#ffb627]" />
          </div>
          <div>
            <h1 className="text-sm font-bold font-display tracking-tight text-[#eceff3]">
              COSMOHUB <span className="text-[#ffb627]">INTELLIGENCE WORKSPACE</span>
            </h1>
            <span className="text-[10px] text-[#8891a3]">STAGE 4.3 — RESEARCH SESSIONS & PROVENANCE GRAPH</span>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center space-x-3">
          <button
            onClick={handleCopyResearchSummary}
            disabled={!currentSession}
            className="px-3 py-1.5 rounded bg-[#171c27] border border-[#4ce0c6] text-[#4ce0c6] hover:bg-[#4ce0c6] hover:text-[#0b0e14] text-xs font-bold transition-all flex items-center gap-1.5 disabled:opacity-50"
          >
            {copiedSummary ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copiedSummary ? "SUMMARY COPIED" : "COPY RESEARCH SUMMARY"}</span>
          </button>
        </div>
      </header>

      {/* Main 3-Column Intelligence Workspace Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-0 min-h-[calc(100vh-60px)]">
        
        {/* COLUMN 1: LEFT INVESTIGATION SIDEBAR (3 Cols) */}
        <div className="lg:col-span-3">
          <InvestigationSidebar
            session={currentSession}
            sessionsList={sessionsList}
            activeEntityFilter={activeEntityFilter}
            onSelectEntityFilter={setActiveEntityFilter}
            onSelectSession={handleSelectSession}
            onCreateNewSession={handleCreateNewSession}
            onDeleteSession={handleDeleteSession}
          />
        </div>

        {/* COLUMN 2: CENTER RESEARCH WORKSPACE (9 Cols) */}
        <div className="lg:col-span-9 p-6 space-y-6 overflow-y-auto">
          
          {/* Top Mode View Selector Tabs */}
          <div className="flex items-center justify-between border-b border-[#232838] pb-3">
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setViewMode("workspace")}
                className={`px-4 py-2 rounded text-xs font-bold transition-all flex items-center gap-2 border ${
                  viewMode === "workspace"
                    ? "bg-[#171c27] border-[#ffb627] text-[#ffb627]"
                    : "bg-[#0b0e14] border-[#232838] text-[#8891a3] hover:border-[#384158]"
                }`}
              >
                <BarChart2 className="w-4 h-4" />
                <span>RESEARCH WORKSPACE</span>
              </button>

              <button
                onClick={() => setViewMode("comparison")}
                className={`px-4 py-2 rounded text-xs font-bold transition-all flex items-center gap-2 border ${
                  viewMode === "comparison"
                    ? "bg-[#171c27] border-[#4ce0c6] text-[#4ce0c6]"
                    : "bg-[#0b0e14] border-[#232838] text-[#8891a3] hover:border-[#384158]"
                }`}
              >
                <Table className="w-4 h-4" />
                <span>ENTITY COMPARISON MATRIX</span>
              </button>

              <button
                onClick={() => setViewMode("graph")}
                className={`px-4 py-2 rounded text-xs font-bold transition-all flex items-center gap-2 border ${
                  viewMode === "graph"
                    ? "bg-[#171c27] border-[#ffb627] text-[#ffb627]"
                    : "bg-[#0b0e14] border-[#232838] text-[#8891a3] hover:border-[#384158]"
                }`}
              >
                <Network className="w-4 h-4" />
                <span>2D KNOWLEDGE GRAPH</span>
              </button>
            </div>
          </div>

          {/* Search Query Area */}
          <QueryInput
            value={queryValue}
            onSearch={handleExecuteResearch}
            isLoading={isLoading}
          />

          {/* Error Banner */}
          {errorMsg && (
            <div className="p-4 bg-[#1f1616] border border-[#7a2a2a] rounded-lg text-xs font-mono text-[#ff6b6b] space-y-1">
              <div className="font-bold flex items-center gap-2">
                <AlertTriangle className="w-4 h-4" />
                <span>RESEARCH ERROR</span>
              </div>
              <p className="font-sans">{errorMsg}</p>
            </div>
          )}

          {/* Execution Stepper */}
          {isLoading && (
            <ProcessStepper
              isLoading={isLoading}
              currentStepIndex={activeStepIndex}
            />
          )}

          {/* MODE 1: RESEARCH WORKSPACE VIEW */}
          {viewMode === "workspace" && currentSession && (
            <div className="space-y-6">
              
              {/* Evidence Density Bar */}
              <div className="p-4 rounded-lg bg-[#12161f] border border-[#232838] space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-[#4ce0c6] tracking-wider uppercase">
                    EVIDENCE DENSITY ({currentSession.metadata.evidence_density}%)
                  </span>
                  <span className="text-[#8891a3]">
                    {currentSession.metadata.supported_count} VERIFIED PROPOSITIONS / {currentSession.metadata.total_propositions} TOTAL
                  </span>
                </div>

                <div className="w-full bg-[#0b0e14] h-2 rounded-full overflow-hidden border border-[#232838]">
                  <div
                    className="bg-[#4ce0c6] h-full transition-all duration-500"
                    style={{ width: `${currentSession.metadata.evidence_density}%` }}
                  ></div>
                </div>

                <div className="flex flex-wrap items-center gap-4 text-[11px] text-[#8891a3] pt-1 border-t border-[#232838]">
                  <span>Tier-1 Sources: <strong className="text-[#ffb627]">{currentSession.metadata.tier1_source_count}</strong></span>
                  <span>Corroborated Props: <strong className="text-[#eceff3]">{currentSession.metadata.corroboration_count}</strong></span>
                  <span>Insufficient Props: <strong className="text-[#ff6b6b]">{currentSession.metadata.insufficient_count}</strong></span>
                </div>
              </div>

              {/* Proposition Status Filter Pills */}
              <div className="flex flex-wrap items-center gap-2 pt-2 border-b border-[#232838] pb-3 text-xs">
                <span className="text-[10px] text-[#8891a3] font-bold uppercase tracking-wider mr-2">FILTER PROPOSITIONS:</span>
                {["ALL", "SUPPORTED", "INSUFFICIENT_EVIDENCE", "CONTRADICTED", "CONFLICT", "REDIRECT_MISMATCH"].map((st) => (
                  <button
                    key={st}
                    onClick={() => setPropStatusFilter(st)}
                    className={`px-3 py-1 rounded border font-bold text-[10.5px] transition-all ${
                      propStatusFilter === st
                        ? "bg-[#171c27] border-[#ffb627] text-[#ffb627]"
                        : "bg-[#0b0e14] border-[#232838] text-[#8891a3] hover:border-[#384158]"
                    }`}
                  >
                    {st.replace('_', ' ')}
                  </button>
                ))}
              </div>

              {/* Recent Grounded Synthesized Answer */}
              {currentSession.queries.length > 0 && (
                <div className="bg-[#12161f] border border-[#232838] p-5 rounded-lg space-y-3 shadow-xl">
                  <div className="flex items-center justify-between border-b border-[#232838] pb-2">
                    <span className="text-xs font-bold text-[#ffb627] tracking-wider uppercase flex items-center gap-1.5">
                      <Sparkles className="w-4 h-4 text-[#ffb627]" />
                      GROUNDED SYNTHESIS (QUERY {currentSession.queries.length})
                    </span>
                    <span className="text-[10px] text-[#8891a3]">RUN ID: {currentSession.queries[currentSession.queries.length - 1].run_id}</span>
                  </div>
                  <p className="text-xs font-sans leading-relaxed text-[#eceff3] whitespace-pre-wrap">
                    {currentSession.queries[currentSession.queries.length - 1].answer}
                  </p>
                </div>
              )}

              {/* Investigated Propositions Grid */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold text-[#eceff3] tracking-wide uppercase">
                    SESSION PROPOSITIONS ({filteredPropositions.length})
                  </h3>
                  <span className="text-[10px] text-[#8891a3]">CLICK "WHY THIS CONCLUSION?" TO INSPECT</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {filteredPropositions.map((prop) => (
                    <PropositionCard
                      key={prop.proposition_id}
                      proposition={prop}
                      onInspectEvidenceChain={handleInspectEvidenceChain}
                    />
                  ))}
                </div>
              </div>

            </div>
          )}

          {/* MODE 2: ENTITY COMPARISON MATRIX VIEW */}
          {viewMode === "comparison" && currentSession && (
            <EntityComparisonView session={currentSession} />
          )}

          {/* MODE 3: 2D KNOWLEDGE GRAPH VIEW */}
          {viewMode === "graph" && currentSession && (
            <EvidenceGraphView
              session={currentSession}
              onInspectProposition={handleInspectEvidenceChain}
            />
          )}

        </div>

      </div>

      {/* COLUMN 3 / MODAL: EVIDENCE EXPLORER (Right Drawer) */}
      <EvidenceExplorerModal
        chainData={selectedChain}
        isLoading={isChainLoading}
        onClose={() => setSelectedChain(null)}
      />

    </div>
  );
}
