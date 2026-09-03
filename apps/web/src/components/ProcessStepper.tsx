import React from "react";
import { ReasoningStep } from "@/lib/types";
import { CheckCircle2, Loader2, Circle } from "lucide-react";

interface ProcessStepperProps {
  steps?: ReasoningStep[];
  isLoading: boolean;
  currentStepIndex: number;
}

export const ProcessStepper: React.FC<ProcessStepperProps> = ({
  steps = [],
  isLoading,
  currentStepIndex,
}) => {
  if (!isLoading && steps.length === 0 && currentStepIndex === 0) return null;

  const defaultStepLabels = [
    { label: "QUERY PLAN", desc: "Intent & entity extraction" },
    { label: "PROPOSITION EXTRACTION", desc: "Structured query targets" },
    { label: "EVIDENCE RETRIEVAL", desc: "Dense + BM25 RRF search" },
    { label: "SEMANTIC VERIFICATION", desc: "5-dimension entailment" },
    { label: "EVIDENCE ASSEMBLY", desc: "Orvyra graph statement mapping" },
    { label: "SYNTHESIS", desc: "Grounded LLM claim validation" },
  ];

  const displaySteps = steps.length > 0 ? steps : defaultStepLabels.map((s, idx) => ({
    step_number: idx + 1,
    label: s.label,
    description: s.desc,
    timestamp: "",
  }));

  return (
    <div className="bg-[#12161f] border border-[#232838] p-4 rounded-lg font-mono mb-6 shadow-md">
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-[#232838] text-xs text-[#8891a3]">
        <span className="text-[#ffb627] font-semibold tracking-wider flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[#ffb627] animate-ping" />
          RESEARCH EXECUTION LIFECYCLE
        </span>
        <span>{isLoading ? "EXECUTING PIPELINE..." : "PIPELINE COMPLETE (100% VERIFIED)"}</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2">
        {displaySteps.map((step, idx) => {
          const isDone = !isLoading || idx < currentStepIndex;
          const isCurrent = isLoading && idx === currentStepIndex;

          return (
            <div
              key={idx}
              className={`p-2.5 rounded border text-[11px] transition-all ${
                isDone
                  ? "bg-[#171c27] border-[#2f6b60] text-[#eceff3]"
                  : isCurrent
                  ? "bg-[#171c27] border-[#8a6a2a] text-[#ffb627] ring-1 ring-[#ffb627]/30"
                  : "bg-[#0a0d12]/50 border-[#232838] text-[#8891a3]"
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-[9px] opacity-70">STEP 0{idx + 1}</span>
                {isDone ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#4ce0c6]" />
                ) : isCurrent ? (
                  <Loader2 className="w-3.5 h-3.5 text-[#ffb627] animate-spin" />
                ) : (
                  <Circle className="w-3 h-3 text-[#8891a3]/40" />
                )}
              </div>
              <div className="font-bold tracking-tight truncate font-display">{step.label}</div>
              <div className="text-[9.5px] opacity-60 truncate mt-0.5 font-sans">{step.description}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
