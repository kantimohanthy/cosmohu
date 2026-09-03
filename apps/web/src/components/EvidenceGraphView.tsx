import React, { useState } from "react";
import { ResearchSession } from "@/lib/types";
import { Layers, ShieldCheck, FileText, Database, Globe, Info } from "lucide-react";

interface EvidenceGraphViewProps {
  session: ResearchSession;
  onInspectProposition: (propId: string) => void;
}

interface GraphNode {
  id: string;
  type: "ENTITY" | "CLAIM" | "EVIDENCE" | "DOCUMENT" | "SOURCE";
  label: string;
  x: number;
  y: number;
  data: any;
}

interface GraphEdge {
  from: string;
  to: string;
}

export const EvidenceGraphView: React.FC<EvidenceGraphViewProps> = ({ session, onInspectProposition }) => {
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  // Construct 2D Graph Nodes & Edges strictly from verified backend propositions & evidence references
  const nodes: GraphNode[] = [];
  const edges: GraphEdge[] = [];

  const supportedProps = session.propositions.filter((p) => p.status === "SUPPORTED");

  // Step 1: Entity Nodes (x: 100)
  session.entities.forEach((ent, idx) => {
    nodes.push({
      id: `ent_${ent.entity_id}`,
      type: "ENTITY",
      label: ent.entity_name,
      x: 100,
      y: 100 + idx * 110,
      data: ent
    });
  });

  // Step 2: Claim Nodes (x: 320)
  session.supported_claims.forEach((clm, idx) => {
    const claimNodeId = clm.claim_id;
    nodes.push({
      id: claimNodeId,
      type: "CLAIM",
      label: clm.text,
      x: 320,
      y: 100 + idx * 110,
      data: clm
    });

    // Edge: ENTITY -> CLAIM
    const entNodeId = `ent_${clm.entity_id}`;
    if (nodes.some((n) => n.id === entNodeId)) {
      edges.push({ from: entNodeId, to: claimNodeId });
    }
  });

  // Step 3: Evidence Nodes (x: 540)
  session.evidence_references.forEach((ev, idx) => {
    const evNodeId = ev.evidence_id;
    nodes.push({
      id: evNodeId,
      type: "EVIDENCE",
      label: `Evidence (${ev.source_tier})`,
      x: 540,
      y: 80 + idx * 90,
      data: ev
    });

    // Edge: CLAIM -> EVIDENCE
    const clmNodeId = `clm_${ev.proposition_id.replace('PROP-', '').split('-')[0].toLowerCase()}_reusable`;
    if (nodes.some((n) => n.id === clmNodeId)) {
      edges.push({ from: clmNodeId, to: evNodeId });
    }
  });

  // Step 4: Document Nodes (x: 740)
  session.evidence_references.forEach((ev, idx) => {
    const docNodeId = ev.document_id;
    if (!nodes.some((n) => n.id === docNodeId)) {
      nodes.push({
        id: docNodeId,
        type: "DOCUMENT",
        label: `Doc ${docNodeId.slice(0, 12)}`,
        x: 740,
        y: 80 + idx * 90,
        data: ev
      });

      // Edge: EVIDENCE -> DOCUMENT
      edges.push({ from: ev.evidence_id, to: docNodeId });
    }
  });

  // Step 5: Source Nodes (x: 940)
  session.source_references.forEach((src, idx) => {
    const srcNodeId = src.source_id;
    if (!nodes.some((n) => n.id === srcNodeId)) {
      nodes.push({
        id: srcNodeId,
        type: "SOURCE",
        label: src.publisher,
        x: 940,
        y: 100 + idx * 110,
        data: src
      });

      // Edge: DOCUMENT -> SOURCE
      session.evidence_references.forEach((ev) => {
        if (ev.source_url === src.source_url) {
          edges.push({ from: ev.document_id, to: srcNodeId });
        }
      });
    }
  });

  const getNodeColor = (type: string) => {
    switch (type) {
      case "ENTITY":
        return "#4ce0c6";
      case "CLAIM":
        return "#ffb627";
      case "EVIDENCE":
        return "#eceff3";
      case "DOCUMENT":
        return "#8891a3";
      case "SOURCE":
        return "#4ce0c6";
      default:
        return "#8891a3";
    }
  };

  return (
    <div className="space-y-4 font-mono text-[#eceff3]">
      {/* Header Banner */}
      <div className="p-4 rounded-lg bg-[#12161f] border border-[#232838] space-y-2">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold font-display text-[#eceff3] tracking-wide">
            2D EVIDENCE RELATIONSHIP KNOWLEDGE GRAPH
          </h2>
          <span className="text-xs text-[#ffb627] font-bold bg-[#171c27] px-3 py-1 rounded border border-[#8a6a2a]">
            VERIFIED BACKEND EDGES ONLY
          </span>
        </div>
        <p className="text-xs text-[#8891a3] font-sans">
          Interactive 2D graph visualizing canonical relationships ($\text{ENTITY} \rightarrow \text{CLAIM} \rightarrow \text{EVIDENCE} \rightarrow \text{DOCUMENT} \rightarrow \text{SOURCE}$). Unsupported propositions do NOT appear as graph edges.
        </p>
      </div>

      {/* SVG Canvas Workspace */}
      <div className="relative border border-[#232838] rounded-lg bg-[#0b0e14] overflow-x-auto shadow-2xl p-4 min-h-[450px]">
        <svg className="w-[1050px] h-[420px]">
          {/* Render Edges */}
          {edges.map((e, idx) => {
            const sourceNode = nodes.find((n) => n.id === e.from);
            const targetNode = nodes.find((n) => n.id === e.to);
            if (!sourceNode || !targetNode) return null;

            const isHighlighted = selectedNode && (selectedNode.id === e.from || selectedNode.id === e.to);

            return (
              <line
                key={idx}
                x1={sourceNode.x}
                y1={sourceNode.y}
                x2={targetNode.x}
                y2={targetNode.y}
                stroke={isHighlighted ? "#ffb627" : "#232838"}
                strokeWidth={isHighlighted ? 2.5 : 1.5}
                strokeDasharray={isHighlighted ? "none" : "3,3"}
              />
            );
          })}

          {/* Render Nodes */}
          {nodes.map((node) => {
            const isSelected = selectedNode?.id === node.id;
            const color = getNodeColor(node.type);

            return (
              <g
                key={node.id}
                transform={`translate(${node.x}, ${node.y})`}
                onClick={() => setSelectedNode(node)}
                className="cursor-pointer group"
              >
                <circle
                  r={isSelected ? 16 : 12}
                  fill="#12161f"
                  stroke={color}
                  strokeWidth={isSelected ? 3 : 2}
                  className="transition-all hover:scale-125"
                />
                <text
                  y={24}
                  textAnchor="middle"
                  fill={isSelected ? "#ffb627" : "#eceff3"}
                  fontSize={10}
                  fontFamily="monospace"
                  fontWeight="bold"
                >
                  {node.label.slice(0, 18)}
                </text>
                <text
                  y={-18}
                  textAnchor="middle"
                  fill={color}
                  fontSize={8}
                  fontFamily="monospace"
                >
                  {node.type}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Selected Node Details Card */}
        {selectedNode && (
          <div className="mt-4 p-4 rounded bg-[#171c27] border border-[#ffb627] space-y-2 text-xs">
            <div className="flex items-center justify-between border-b border-[#ffb627]/40 pb-2">
              <span className="font-bold text-[#ffb627]">SELECTED NODE: {selectedNode.type}</span>
              <button onClick={() => setSelectedNode(null)} className="text-[10px] text-[#8891a3] hover:text-[#eceff3]">
                DISMISS
              </button>
            </div>
            <div className="space-y-1 font-sans">
              <div><strong className="text-[#8891a3]">LABEL:</strong> {selectedNode.label}</div>
              <div><strong className="text-[#8891a3]">NODE ID:</strong> <span className="font-mono text-[#4ce0c6]">{selectedNode.id}</span></div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
