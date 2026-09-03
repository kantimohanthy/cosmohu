import React from "react";
import { WhyCategory } from "@/lib/types";
import { HelpCircle, ChevronRight } from "lucide-react";

interface WhySectionProps {
  categories: WhyCategory[];
  onSelectSnippet?: (snippet: string) => void;
}

export const WhySection: React.FC<WhySectionProps> = ({ categories, onSelectSnippet }) => {
  if (!categories || categories.length === 0) return null;

  return (
    <div className="bg-[#12161f] border border-[#232838] p-5 rounded-lg font-mono mb-6">
      <div className="flex items-center space-x-2 text-xs font-semibold text-[#ffb627] tracking-wider mb-4 pb-2 border-b border-[#232838]">
        <HelpCircle className="w-4 h-4 text-[#ffb627]" />
        <span>WHY THIS CONCLUSION</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {categories.map((cat, idx) => (
          <div
            key={idx}
            className="bg-[#171c27] border border-[#232838] p-4 rounded-lg flex flex-col justify-between hover:border-[#8a6a2a] transition-all"
          >
            <div>
              <div className="text-[10px] text-[#ffb627] font-semibold tracking-wider mb-1">
                {cat.code}
              </div>
              <div className="text-xs font-bold text-[#eceff3] mb-2 font-sans">{cat.title}</div>
              <div className="text-xs text-[#8891a3] leading-relaxed mb-3">{cat.summary}</div>
            </div>

            {cat.evidence_snippets && cat.evidence_snippets.length > 0 && (
              <div className="pt-2 border-t border-[#232838]/60 space-y-1.5">
                <span className="text-[9.5px] text-[#4ce0c6] uppercase tracking-wider block">
                  KEY EVIDENCE SNIPPET:
                </span>
                {cat.evidence_snippets.map((snip, sIdx) => (
                  <div
                    key={sIdx}
                    onClick={() => onSelectSnippet && onSelectSnippet(snip)}
                    className="text-[10.5px] text-[#eceff3] bg-[#0a0d12] p-2 rounded border border-[#232838] hover:border-[#4ce0c6] cursor-pointer transition-colors flex items-start justify-between gap-1 group"
                  >
                    <span className="line-clamp-2">"{snip}"</span>
                    <ChevronRight className="w-3 h-3 text-[#8891a3] group-hover:text-[#4ce0c6] shrink-0 mt-0.5" />
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
