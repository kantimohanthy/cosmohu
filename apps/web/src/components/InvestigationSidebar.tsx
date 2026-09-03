import React from "react";
import { ResearchSession } from "@/lib/types";
import { FolderPlus, Layers, Database, ShieldCheck, AlertTriangle, HelpCircle, FileText, Globe, ChevronRight, PlusCircle, Trash2 } from "lucide-react";

interface InvestigationSidebarProps {
  session: ResearchSession | null;
  sessionsList: ResearchSession[];
  activeEntityFilter: string | null;
  onSelectEntityFilter: (entityId: string | null) => void;
  onSelectSession: (sessionId: string) => void;
  onCreateNewSession: () => void;
  onDeleteSession: (sessionId: string) => void;
}

export const InvestigationSidebar: React.FC<InvestigationSidebarProps> = ({
  session,
  sessionsList,
  activeEntityFilter,
  onSelectEntityFilter,
  onSelectSession,
  onCreateNewSession,
  onDeleteSession,
}) => {
  if (!session) {
    return (
      <div className="w-full h-full p-4 bg-[#12161f] border-r border-[#232838] font-mono text-[#eceff3] space-y-4">
        <div className="flex items-center justify-between border-b border-[#232838] pb-3">
          <span className="text-xs font-bold text-[#ffb627] tracking-wider uppercase">INVESTIGATION SIDEBAR</span>
          <button
            onClick={onCreateNewSession}
            className="p-1.5 rounded bg-[#171c27] border border-[#ffb627] text-[#ffb627] hover:bg-[#ffb627] hover:text-[#0b0e14] transition-all flex items-center gap-1 text-xs font-bold"
          >
            <PlusCircle className="w-3.5 h-3.5" />
            <span>NEW</span>
          </button>
        </div>
        <p className="text-xs text-[#8891a3] italic">No active research session selected.</p>
      </div>
    );
  }

  const meta = session.metadata;

  return (
    <div className="w-full h-full p-4 bg-[#12161f] border-r border-[#232838] font-mono text-[#eceff3] space-y-6 overflow-y-auto">
      
      {/* Session Title & Switcher Header */}
      <div className="space-y-3 pb-3 border-b border-[#232838]">
        <div className="flex items-center justify-between">
          <span className="text-[10px] text-[#ffb627] font-bold tracking-widest uppercase">CURRENT INVESTIGATION</span>
          <button
            onClick={onCreateNewSession}
            className="px-2.5 py-1 rounded bg-[#171c27] border border-[#ffb627] text-[#ffb627] hover:bg-[#ffb627] hover:text-[#0b0e14] transition-all flex items-center gap-1 text-[10.5px] font-bold"
          >
            <PlusCircle className="w-3 h-3" />
            <span>NEW</span>
          </button>
        </div>

        <div className="space-y-1">
          <h2 className="text-sm font-bold text-[#eceff3] font-display line-clamp-2">{session.title}</h2>
          <div className="text-[10px] text-[#8891a3]">
            ID: <span className="text-[#eceff3]">{session.session_id}</span>
          </div>
        </div>

        {/* Sessions Dropdown List */}
        {sessionsList.length > 1 && (
          <div className="pt-1">
            <select
              value={session.session_id}
              onChange={(e) => onSelectSession(e.target.value)}
              className="w-full p-1.5 rounded bg-[#0b0e14] border border-[#232838] text-xs text-[#eceff3] font-mono focus:border-[#ffb627] outline-none"
            >
              {sessionsList.map((s) => (
                <option key={s.session_id} value={s.session_id}>
                  {s.title.slice(0, 35)}... ({s.queries.length} Qs)
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Real Session Metrics Summary Grid */}
      <div className="space-y-2">
        <span className="text-[10px] text-[#8891a3] font-bold tracking-wider uppercase">SESSION METRICS</span>
        <div className="grid grid-cols-2 gap-1.5 text-xs">
          <div className="p-2 rounded bg-[#0b0e14] border border-[#232838]">
            <span className="text-[9.5px] text-[#8891a3] block">QUERIES</span>
            <span className="font-bold text-[#eceff3] text-sm">{meta.total_queries}</span>
          </div>
          <div className="p-2 rounded bg-[#0b0e14] border border-[#232838]">
            <span className="text-[9.5px] text-[#8891a3] block">ENTITIES</span>
            <span className="font-bold text-[#4ce0c6] text-sm">{meta.total_entities}</span>
          </div>
          <div className="p-2 rounded bg-[#0b0e14] border border-[#232838]">
            <span className="text-[9.5px] text-[#4ce0c6] block">SUPPORTED</span>
            <span className="font-bold text-[#4ce0c6] text-sm">{meta.supported_count}</span>
          </div>
          <div className="p-2 rounded bg-[#0b0e14] border border-[#232838]">
            <span className="text-[9.5px] text-[#ffb627] block">INSUFFICIENT</span>
            <span className="font-bold text-[#ffb627] text-sm">{meta.insufficient_count}</span>
          </div>
        </div>
      </div>

      {/* Discovered Entities Filter Section */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-[10px] text-[#8891a3] font-bold tracking-wider uppercase">DISCOVERED ENTITIES</span>
          {activeEntityFilter && (
            <button
              onClick={() => onSelectEntityFilter(null)}
              className="text-[9.5px] text-[#ffb627] hover:underline"
            >
              CLEAR FILTER
            </button>
          )}
        </div>

        <div className="space-y-1">
          <button
            onClick={() => onSelectEntityFilter(null)}
            className={`w-full p-2 rounded text-left text-xs font-mono transition-all flex items-center justify-between border ${
              activeEntityFilter === null
                ? "bg-[#171c27] border-[#4ce0c6] text-[#4ce0c6]"
                : "bg-[#0b0e14] border-[#232838] text-[#8891a3] hover:border-[#384158]"
            }`}
          >
            <span>ALL ENTITIES</span>
            <span className="text-[10px] font-bold">{session.propositions.length}</span>
          </button>

          {session.entities.map((ent) => {
            const isSelected = activeEntityFilter === ent.entity_id;
            const count = session.propositions.filter((p) => p.entity_id === ent.entity_id).length;
            return (
              <button
                key={ent.entity_id}
                onClick={() => onSelectEntityFilter(ent.entity_id)}
                className={`w-full p-2 rounded text-left text-xs font-mono transition-all flex items-center justify-between border ${
                  isSelected
                    ? "bg-[#171c27] border-[#ffb627] text-[#ffb627]"
                    : "bg-[#0b0e14] border-[#232838] text-[#eceff3] hover:border-[#384158]"
                }`}
              >
                <span className="truncate">{ent.entity_name}</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#232838] text-[#8891a3] font-bold">{count}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Submitted Queries List */}
      <div className="space-y-2">
        <span className="text-[10px] text-[#8891a3] font-bold tracking-wider uppercase">INVESTIGATION QUERIES ({session.queries.length})</span>
        <div className="space-y-1 max-h-48 overflow-y-auto pr-1">
          {session.queries.map((q, idx) => (
            <div key={q.query_id} className="p-2 rounded bg-[#0b0e14] border border-[#232838] text-[11px] font-mono space-y-1">
              <div className="flex items-center justify-between text-[9.5px] text-[#8891a3]">
                <span>Q0{idx + 1}</span>
                <span className="text-[#4ce0c6]">{q.status}</span>
              </div>
              <p className="text-[#eceff3] font-sans text-xs line-clamp-2">"{q.query_text}"</p>
            </div>
          ))}
        </div>
      </div>

      {/* Delete Session Button */}
      <div className="pt-4 border-t border-[#232838]">
        <button
          onClick={() => onDeleteSession(session.session_id)}
          className="w-full py-2 px-3 rounded bg-[#1f1616] border border-[#7a2a2a] hover:bg-[#7a2a2a] hover:text-[#eceff3] text-[#ff6b6b] text-xs font-mono font-bold transition-all flex items-center justify-center gap-1.5"
        >
          <Trash2 className="w-3.5 h-3.5" />
          <span>DELETE INVESTIGATION</span>
        </button>
      </div>

    </div>
  );
};
