import React from "react";
import { AnswerResponse, EvidencePassage } from "@/lib/types";
import { ShieldCheck, AlertTriangle, ExternalLink, Sparkles } from "lucide-react";

interface AnswerSectionProps {
  answerData: AnswerResponse;
  onSelectPassage: (passage: EvidencePassage) => void;
}

export const AnswerSection: React.FC<AnswerSectionProps> = ({
  answerData,
  onSelectPassage,
}) => {
  const isSupported = answerData.status === "supported" || answerData.status === "partially_supported";

  return (
    <div className="bg-[#12161f] border border-[#232838] p-6 rounded-lg font-mono mb-6 shadow-xl">
      {/* Top Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 mb-4 border-b border-[#232838]">
        <div className="flex items-center space-x-3">
          <div className="p-1.5 rounded bg-[#171c27] border border-[#8a6a2a]">
            <Sparkles className="w-4 h-4 text-[#ffb627]" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-[#eceff3] tracking-wide font-display">
              GROUNDED RESEARCH SYNTHESIS
            </h2>
            <span className="text-[10px] text-[#8891a3]">
              QUERY: "{answerData.query}"
            </span>
          </div>
        </div>

        {/* Status Badge */}
        <div className="flex items-center space-x-3">
          <div
            className={`px-3 py-1 rounded text-xs font-bold tracking-wider uppercase border flex items-center gap-1.5 ${
              isSupported
                ? "bg-[#171c27] border-[#2f6b60] text-[#4ce0c6]"
                : "bg-[#1f1616] border-[#7a2a2a] text-[#ff6b6b]"
            }`}
          >
            {isSupported ? (
              <ShieldCheck className="w-3.5 h-3.5" />
            ) : (
              <AlertTriangle className="w-3.5 h-3.5" />
            )}
            <span>{answerData.status.replace("_", " ")}</span>
          </div>

          <div className="bg-[#171c27] border border-[#232838] px-3 py-1 rounded text-xs">
            <span className="text-[#8891a3]">CONFIDENCE: </span>
            <span className="text-[#ffb627] font-bold">
              {(answerData.confidence * 100).toFixed(0)}%
            </span>
          </div>
        </div>
      </div>

      {/* Answer Paragraphs */}
      <div className="text-sm leading-relaxed text-[#eceff3] space-y-4 font-sans border-b border-[#232838] pb-6">
        {answerData.answer.split("\n\n").map((para, idx) => (
          <p key={idx} className="whitespace-pre-wrap">
            {para}
          </p>
        ))}
      </div>

      {/* Inspectable Sources Bar */}
      {answerData.sources && answerData.sources.length > 0 && (
        <div className="pt-4">
          <div className="text-xs text-[#8891a3] uppercase tracking-wider mb-3 font-semibold flex items-center justify-between">
            <span>INSPECTABLE EVIDENCE SOURCES ({answerData.sources.length})</span>
            <span className="text-[10px] text-[#4ce0c6]">CLICK PASSAGE TO INSPECT PROVENANCE</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {answerData.sources.map((src, idx) => (
              <div
                key={idx}
                onClick={() => onSelectPassage(src)}
                className="p-3 rounded bg-[#171c27] border border-[#232838] hover:border-[#ffb627] cursor-pointer transition-all flex flex-col justify-between group"
              >
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] text-[#ffb627] font-semibold">
                      SOURCE [{idx + 1}]
                    </span>
                    <span className="text-[9.5px] text-[#4ce0c6]">
                      {(src.confidence_score * 100).toFixed(0)}% CONF
                    </span>
                  </div>
                  <div className="text-xs font-bold text-[#eceff3] truncate font-sans group-hover:text-[#ffb627] transition-colors">
                    {src.title}
                  </div>
                  <div className="text-[10.5px] text-[#8891a3] truncate mt-0.5">
                    {src.publisher}
                  </div>
                </div>

                <div className="mt-2 text-[10px] text-[#4ce0c6] flex items-center justify-between pt-2 border-t border-[#232838]">
                  <span>INSPECT PASSAGE</span>
                  <ExternalLink className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
