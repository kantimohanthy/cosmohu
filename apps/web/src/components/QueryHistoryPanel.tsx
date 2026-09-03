import React from "react";
import { History, Clock, Trash2, ArrowUpRight } from "lucide-react";

export interface QueryHistoryItem {
  query: string;
  timestamp: string;
  supportedCount: number;
}

interface QueryHistoryPanelProps {
  history: QueryHistoryItem[];
  onSelectQuery: (query: string) => void;
  onClearHistory: () => void;
}

export const QueryHistoryPanel: React.FC<QueryHistoryPanelProps> = ({
  history,
  onSelectQuery,
  onClearHistory,
}) => {
  if (!history || history.length === 0) return null;

  return (
    <div className="p-4 rounded-lg bg-[#12161f] border border-[#232838] font-mono text-xs text-[#eceff3] space-y-3 shadow-md">
      <div className="flex items-center justify-between pb-2 border-b border-[#232838]">
        <div className="flex items-center space-x-2 text-[#ffb627] font-bold">
          <History className="w-4 h-4" />
          <span>RESEARCH QUERY HISTORY</span>
        </div>
        <button
          onClick={onClearHistory}
          className="text-[10px] text-[#8891a3] hover:text-[#ff6b6b] flex items-center gap-1 transition-colors"
        >
          <Trash2 className="w-3 h-3" />
          <span>CLEAR HISTORY</span>
        </button>
      </div>

      <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
        {history.map((item, idx) => (
          <div
            key={idx}
            onClick={() => onSelectQuery(item.query)}
            className="p-2.5 rounded bg-[#171c27] border border-[#232838] hover:border-[#ffb627] cursor-pointer transition-all flex items-center justify-between group"
          >
            <div className="truncate pr-2">
              <span className="text-[#eceff3] font-sans font-medium block truncate group-hover:text-[#ffb627] transition-colors">
                "{item.query}"
              </span>
              <span className="text-[10px] text-[#8891a3]">
                {new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} • {item.supportedCount} verified claims
              </span>
            </div>
            <ArrowUpRight className="w-3.5 h-3.5 text-[#ffb627] group-hover:translate-x-0.5 transition-transform flex-shrink-0" />
          </div>
        ))}
      </div>
    </div>
  );
};
