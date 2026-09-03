import React from "react";
import { ClaimItem, EvidencePassage } from "@/lib/types";
import { CheckCircle, ShieldAlert, ArrowUpRight } from "lucide-react";

interface ClaimsTableProps {
  claims: ClaimItem[];
  sources: EvidencePassage[];
  onSelectPassage: (p: EvidencePassage) => void;
}

export const ClaimsTable: React.FC<ClaimsTableProps> = ({
  claims,
  sources,
  onSelectPassage,
}) => {
  if (!claims || claims.length === 0) return null;

  return (
    <div className="bg-[#12161f] border border-[#232838] p-5 rounded-lg font-mono mb-6">
      <div className="flex items-center justify-between pb-3 mb-4 border-b border-[#232838]">
        <span className="text-xs font-semibold text-[#4ce0c6] tracking-wider flex items-center gap-2">
          <CheckCircle className="w-4 h-4 text-[#4ce0c6]" />
          STRUCTURED CLAIM VERIFICATION MATRIX
        </span>
        <span className="text-[10px] text-[#8891a3]">{claims.length} VERIFIED CLAIMS</span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-[#232838] text-[#8891a3] text-[10px] uppercase tracking-wider">
              <th className="py-2.5 px-3">CLAIM IDENTIFIER</th>
              <th className="py-2.5 px-3">GROUNDED STATEMENT</th>
              <th className="py-2.5 px-3 text-center">CONFIDENCE</th>
              <th className="py-2.5 px-3 text-right">SUPPORTING EVIDENCE</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#232838]/60">
            {claims.map((claim, idx) => {
              const matchedPassages = sources.filter((s) => claim.evidence_ids.includes(s.passage_id));
              const firstPassage = matchedPassages[0] || sources[0];

              return (
                <tr key={idx} className="hover:bg-[#171c27] transition-colors">
                  <td className="py-3 px-3 font-semibold text-[#ffb627] whitespace-nowrap">
                    {claim.claim_id.toUpperCase()}
                  </td>
                  <td className="py-3 px-3 text-[#eceff3] max-w-md leading-relaxed font-sans">
                    {claim.text}
                  </td>
                  <td className="py-3 px-3 text-center">
                    <span className="inline-block px-2 py-0.5 rounded bg-[#171c27] border border-[#8a6a2a] text-[#ffb627] font-bold text-[11px]">
                      {(claim.confidence * 100).toFixed(0)}%
                    </span>
                  </td>
                  <td className="py-3 px-3 text-right">
                    {firstPassage && (
                      <button
                        onClick={() => onSelectPassage(firstPassage)}
                        className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-[#171c27] hover:bg-[#232838] border border-[#2f6b60] text-[#4ce0c6] text-[11px] font-mono transition-colors"
                      >
                        <span>{firstPassage.publisher}</span>
                        <ArrowUpRight className="w-3 h-3" />
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
