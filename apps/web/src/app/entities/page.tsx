"use client";

import React, { useEffect, useState } from "react";
import { fetchEntities } from "@/lib/api";
import { Entity } from "@/lib/types";
import { Building2, Rocket, Globe, Shield, Cpu, Tag } from "lucide-react";

export default function EntitiesPage() {
  const [entities, setEntities] = useState<Entity[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchEntities()
      .then((data) => setEntities(data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6 font-mono">
      <div className="flex items-center justify-between pb-4 border-b border-[#232838]">
        <div>
          <h1 className="text-2xl font-bold font-display text-[#eceff3]">SPACE ECONOMY ENTITY DIRECTORY</h1>
          <p className="text-xs text-[#8891a3] font-sans mt-1">
            Companies, launch vehicles, satellite constellations, and agencies in the CosmoHub knowledge graph.
          </p>
        </div>
        <div className="bg-[#171c27] border border-[#8a6a2a] px-3 py-1.5 rounded text-xs text-[#ffb627]">
          {entities.length} INDEXED ENTITIES
        </div>
      </div>

      {loading ? (
        <div className="p-8 text-center text-xs text-[#8891a3]">LOADING ENTITIES DIRECTORY...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {entities.map((ent) => (
            <div
              key={ent.entity_id}
              className="bg-[#12161f] border border-[#232838] p-5 rounded-lg space-y-4 hover:border-[#8a6a2a] transition-all"
            >
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-[10px] text-[#ffb627] font-semibold uppercase tracking-wider block mb-1">
                    {ent.entity_type} • {ent.country || "GLOBAL"}
                  </span>
                  <h3 className="text-lg font-bold text-[#eceff3] font-display">{ent.name}</h3>
                </div>

                {ent.funding_raised_eur_m && (
                  <div className="bg-[#171c27] border border-[#2f6b60] px-3 py-1 rounded text-right">
                    <span className="text-[9px] text-[#8891a3] block">FUNDING RAISED</span>
                    <span className="text-xs font-bold text-[#4ce0c6]">
                      €{ent.funding_raised_eur_m >= 1000 ? `${(ent.funding_raised_eur_m / 1000).toFixed(1)}B` : `${ent.funding_raised_eur_m}M`}
                    </span>
                  </div>
                )}
              </div>

              <p className="text-xs text-[#8891a3] font-sans leading-relaxed">
                {ent.description}
              </p>

              {ent.key_technologies && ent.key_technologies.length > 0 && (
                <div className="pt-3 border-t border-[#232838]">
                  <span className="text-[10px] text-[#8891a3] block mb-2 uppercase tracking-wider">
                    FLAGSHIP TECHNOLOGIES & PLATFORMS:
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {ent.key_technologies.map((tech, tIdx) => (
                      <span
                        key={tIdx}
                        className="px-2.5 py-1 rounded bg-[#171c27] border border-[#232838] text-[10.5px] text-[#eceff3]"
                      >
                        {tech}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
