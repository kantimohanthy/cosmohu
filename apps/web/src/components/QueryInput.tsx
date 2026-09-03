import React, { useState, useEffect } from "react";
import { Search, ArrowRight, Sparkles, X } from "lucide-react";

interface QueryInputProps {
  onSearch: (query: string) => void;
  isLoading: boolean;
  value?: string;
}

export const QueryInput: React.FC<QueryInputProps> = ({ onSearch, isLoading, value = "" }) => {
  const [query, setQuery] = useState(value);

  useEffect(() => {
    if (value) {
      setQuery(value);
    }
  }, [value]);

  const suggestions = [
    "Which European launch companies are developing reusable launch vehicles?",
    "Compare reusable launch vehicle development across European launch companies.",
    "Which European launch companies have ESA-backed development programs?",
    "What is the launch status and reusability of PLD Space MIURA 5?"
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSearch(query.trim());
    }
  };

  const handleClear = () => {
    setQuery("");
  };

  return (
    <div className="w-full max-w-4xl mx-auto mb-8 font-mono">
      <form onSubmit={handleSubmit} className="relative group">
        <div className="relative flex items-center bg-[#12161f] border-2 border-[#232838] focus-within:border-[#ffb627] rounded-xl p-2 transition-all shadow-2xl">
          <div className="pl-3 pr-2 text-[#ffb627]">
            <Search className="w-5 h-5" />
          </div>

          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="What do you want to investigate? (e.g. Which European launch companies are developing reusable launch vehicles?)"
            disabled={isLoading}
            className="w-full bg-transparent text-[#eceff3] placeholder-[#8891a3] text-sm focus:outline-none py-2 px-1 font-sans"
          />

          {query && !isLoading && (
            <button
              type="button"
              onClick={handleClear}
              className="p-1 text-[#8891a3] hover:text-[#eceff3] mr-2"
            >
              <X className="w-4 h-4" />
            </button>
          )}

          <button
            type="submit"
            disabled={!query.trim() || isLoading}
            className="flex items-center space-x-2 px-5 py-2.5 bg-[#ffb627] hover:bg-[#e09e1f] disabled:bg-[#232838] text-[#0a0d12] disabled:text-[#8891a3] font-bold rounded-lg text-xs tracking-wider transition-all font-mono shadow-md flex-shrink-0"
          >
            <span>{isLoading ? "RESEARCHING..." : "RESEARCH"}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </form>

      {/* Suggestions */}
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <span className="text-[10px] text-[#8891a3] uppercase tracking-wider flex items-center gap-1 mr-1">
          <Sparkles className="w-3 h-3 text-[#ffb627]" />
          RESEARCH SUGGESTIONS:
        </span>
        {suggestions.map((sug, idx) => (
          <button
            key={idx}
            onClick={() => {
              setQuery(sug);
              onSearch(sug);
            }}
            disabled={isLoading}
            className="text-[11px] bg-[#12161f] hover:bg-[#171c27] text-[#8891a3] hover:text-[#eceff3] border border-[#232838] hover:border-[#8a6a2a] px-3 py-1 rounded-full transition-colors font-sans truncate max-w-xs text-left"
          >
            {sug}
          </button>
        ))}
      </div>
    </div>
  );
};
