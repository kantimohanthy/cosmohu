import React from "react";
import { ShieldCheck, Database, Rocket, Search } from "lucide-react";

interface ResearchEmptyStateProps {
  onSelectExampleQuery: (query: string) => void;
}

export const ResearchEmptyState: React.FC<ResearchEmptyStateProps> = ({ onSelectExampleQuery }) => {
  const exampleQueries = [
    "Which European launch companies are developing reusable launch vehicles?",
    "Compare reusable launch vehicle development across European launch companies.",
    "Which European launch companies have ESA-backed development programs?",
    "What is the launch status and reusability of PLD Space MIURA 5?"
  ];

  return (
    <div className="space-y-6 pt-4 font-mono">
      {/* Example Queries Section */}
      <div className="p-6 rounded-lg bg-[#12161f] border border-[#232838] space-y-4">
        <div className="flex items-center space-x-2 text-xs font-bold text-[#ffb627]">
          <Search className="w-4 h-4" />
          <span>SUGGESTED RESEARCH INVESTIGATIONS</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {exampleQueries.map((q, idx) => (
            <button
              key={idx}
              onClick={() => onSelectExampleQuery(q)}
              className="p-3.5 rounded bg-[#171c27] border border-[#232838] hover:border-[#ffb627] text-left transition-all text-xs font-sans text-[#eceff3] hover:text-[#ffb627] flex items-start justify-between group"
            >
              <span>"{q}"</span>
              <span className="text-[10px] font-mono text-[#ffb627] ml-2 flex-shrink-0 group-hover:translate-x-0.5 transition-transform">USE →</span>
            </button>
          ))}
        </div>
      </div>

      {/* Core Architectural Invariants */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-5 rounded-lg bg-[#12161f] border border-[#232838] space-y-2">
          <div className="text-[#ffb627] font-mono text-xs font-semibold flex items-center gap-2">
            <ShieldCheck className="w-4 h-4" />
            NO EVIDENCE → NO CLAIM
          </div>
          <h3 className="text-sm font-bold font-display text-[#eceff3]">Zero Hallucination Guarantee</h3>
          <p className="text-xs text-[#8891a3] leading-relaxed font-sans">
            The LLM is an interface layer over knowledge infrastructure. Claims are strictly bound to inspectable sources with SHA-256 provenance.
          </p>
        </div>

        <div className="p-5 rounded-lg bg-[#12161f] border border-[#232838] space-y-2">
          <div className="text-[#4ce0c6] font-mono text-xs font-semibold flex items-center gap-2">
            <Database className="w-4 h-4" />
            HYBRID FUSION ENGINE
          </div>
          <h3 className="text-sm font-bold font-display text-[#eceff3]">Dense + Sparse BM25 + Rerank</h3>
          <p className="text-xs text-[#8891a3] leading-relaxed font-sans">
            Combines semantic vector similarity search with precise keyword term matching and entity-aware cross-encoder candidate reranking.
          </p>
        </div>

        <div className="p-5 rounded-lg bg-[#12161f] border border-[#232838] space-y-2">
          <div className="text-[#ffb627] font-mono text-xs font-semibold flex items-center gap-2">
            <Rocket className="w-4 h-4" />
            SPACE ECONOMY ONTOLOGY
          </div>
          <h3 className="text-sm font-bold font-display text-[#eceff3]">European Launch & Constellations</h3>
          <p className="text-xs text-[#8891a3] leading-relaxed font-sans">
            Pre-loaded with verified data on Isar Aerospace, Rocket Factory Augsburg, MaiaSpace, PLD Space, Orbex, Ariane 6, and IRIS².
          </p>
        </div>
      </div>
    </div>
  );
};
