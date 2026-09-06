import { useEffect, useMemo, useRef } from "react";
import * as d3 from "d3";
import type { GraphLink, GraphNode } from "../../types";

const DOMAIN_COLOR: Record<string, string> = {
  demand: "#f97360",
  production: "#5ab1ff",
  supply: "#3ed0b7",
  planning: "#ffbe55",
};

interface Props {
  nodes: GraphNode[];
  links: GraphLink[];
  selectedNodeId?: string;
  search: string;
  activeDomains: string[];
  onSelect: (node: GraphNode) => void;
}

type SimNode = GraphNode & d3.SimulationNodeDatum;
type SimLink = d3.SimulationLinkDatum<SimNode> & GraphLink;

type ExtendedNode = SimNode & {
  parentId?: string;
  attributeIndex?: number;
  isAttribute?: boolean;
};

type ExtendedLink = SimLink & {
  isAttributeLink?: boolean;
};

const NODE_ATTRIBUTES: Record<string, string[]> = {
  CustomerOrder: ["order_id", "requested_date", "committed_date", "order_priority"],
  Customer: ["priority_level", "penalty_rate", "delivery_reliability"],
  FinishedItem: ["item_category", "safety_stock", "lot_size_rule"],
  WorkCenter: ["standard_capacity", "efficiency_factor", "bottleneck_flag"],
  ProductionOrder: ["planned_end", "forecast_end", "delay_risk_score"],
  Operation: ["op_sequence", "processing_time", "predecessor_ops"],
  Inventory: ["on_hand_qty", "in_transit_qty", "available_qty"],
  BOMLevel: ["quantity_per", "scrap_factor", "alternative_items"],
  Supplier: ["standard_lt", "on_time_rate", "single_source_flag"],
  Routing: ["total_lead_time", "bottleneck_wc", "alternative_routings"],
  ATPCommitment: ["committed_date", "confidence_score", "risk_level"],
};

function getNodeId(node: string | GraphNode | SimNode): string {
  return typeof node === "string" ? node : node.id;
}

export function OntologyGraph({ nodes, links, selectedNodeId, search, activeDomains, onSelect }: Props) {
  const svgRef = useRef<SVGSVGElement | null>(null);

  const filteredIds = useMemo(() => {
    const q = search.trim().toLowerCase();
    return new Set(
      nodes
        .filter((node) => {
          const domainVisible = activeDomains.includes(node.domain);
          if (!domainVisible) {
            return false;
          }
          if (!q) {
            return true;
          }
          return [node.label, node.en, node.desc].some((item) => item.toLowerCase().includes(q));
        })
        .map((node) => node.id),
    );
  }, [activeDomains, nodes, search]);

  useEffect(() => {
    if (!svgRef.current) {
      return;
    }
    const svg = d3.select<SVGSVGElement, unknown>(svgRef.current);
    svg.selectAll("*").remove();
    const width = svgRef.current?.clientWidth ?? 1000;
    const height = svgRef.current?.clientHeight ?? 700;

    const primaryNodes = nodes.map((node) => ({ ...node })) as ExtendedNode[];
    const attributeNodes = nodes.flatMap((node) =>
      (NODE_ATTRIBUTES[node.id] ?? []).map(
        (attribute, index) =>
          ({
            id: `${node.id}::${attribute}`,
            label: attribute,
            en: "Attribute",
            domain: node.domain,
            size: 12,
            desc: `${node.label} 的核心属性`,
            parentId: node.id,
            attributeIndex: index,
            isAttribute: true,
          }) as ExtendedNode,
      ),
    );
    const simNodes = [...primaryNodes, ...attributeNodes] as ExtendedNode[];
    const simLinks = [
      ...links.map((link) => ({ ...link })),
      ...attributeNodes.map(
        (node) =>
          ({
            source: node.parentId,
            target: node.id,
            label: "has_attribute",
            domain: node.domain,
            isAttributeLink: true,
          }) as ExtendedLink,
      ),
    ] as ExtendedLink[];

    const root = svg.append("g");
    const zoomBehavior = d3.zoom<SVGSVGElement, unknown>().scaleExtent([0.35, 3]).on("zoom", (event) => {
      root.attr("transform", event.transform.toString());
    });
    svg.call(zoomBehavior as unknown as (selection: d3.Selection<SVGSVGElement, unknown, null, undefined>) => void);

    const simulation = d3
      .forceSimulation<ExtendedNode>(simNodes)
      .force("link", d3.forceLink<ExtendedNode, ExtendedLink>(simLinks).id((d) => d.id).distance((d) => (d.isAttributeLink ? 70 : 150)).strength((d) => (d.isAttributeLink ? 0.9 : 0.55)))
      .force("charge", d3.forceManyBody<ExtendedNode>().strength((d: ExtendedNode) => (d.isAttribute ? -120 : -700)))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide<ExtendedNode>().radius((d) => d.size + (d.isAttribute ? 6 : 12)));

    const attributePosition = ((alpha: number) => {
      const nodeMap = new Map(simNodes.map((node) => [node.id, node]));
      for (const node of simNodes) {
        if (!node.isAttribute || !node.parentId) {
          continue;
        }
        const parent = nodeMap.get(node.parentId);
        if (!parent) {
          continue;
        }
        const angle = ((node.attributeIndex ?? 0) / Math.max((NODE_ATTRIBUTES[node.parentId] ?? []).length, 1)) * Math.PI * 2;
        const radius = parent.size + 54;
        const targetX = (parent.x ?? width / 2) + Math.cos(angle) * radius;
        const targetY = (parent.y ?? height / 2) + Math.sin(angle) * radius;
        node.vx = (node.vx ?? 0) + (targetX - (node.x ?? targetX)) * 0.1 * alpha;
        node.vy = (node.vy ?? 0) + (targetY - (node.y ?? targetY)) * 0.1 * alpha;
      }
    }) as d3.Force<ExtendedNode, ExtendedLink>;
    simulation.force("attributePosition", attributePosition);

    const link = root
      .append("g")
      .selectAll("path")
      .data(simLinks)
      .join("path")
      .attr("fill", "none")
      .attr("stroke", (d) => (d.isAttributeLink ? "rgba(255,255,255,0.92)" : DOMAIN_COLOR[d.domain] ?? "#777"))
      .attr("stroke-opacity", (d) => {
        const source = getNodeId(d.source as string | GraphNode | SimNode);
        const target = getNodeId(d.target as string | GraphNode | SimNode);
        if (d.isAttributeLink) {
          return filteredIds.has(source) ? 0.95 : 0.18;
        }
        return filteredIds.has(source) && filteredIds.has(target) ? 0.45 : 0.06;
      })
      .attr("stroke-width", (d) => (d.isAttributeLink ? 1 : 1.5))
      .attr("stroke-dasharray", (d) => (d.isAttributeLink ? "3,3" : "0"));

    const linkLabels = root
      .append("g")
      .selectAll("text")
      .data(simLinks.filter((link) => !link.isAttributeLink))
      .join("text")
      .attr("fill", (d) => DOMAIN_COLOR[d.domain] ?? "#aaa")
      .attr("font-size", 10)
      .attr("font-weight", 600)
      .attr("text-anchor", "middle")
      .attr("pointer-events", "none")
      .attr("opacity", (d) => {
        const source = getNodeId(d.source as string | GraphNode | SimNode);
        const target = getNodeId(d.target as string | GraphNode | SimNode);
        return filteredIds.has(source) && filteredIds.has(target) ? 0.78 : 0.08;
      })
      .text((d) => d.label);

    const dragBehavior = d3
      .drag<SVGGElement, ExtendedNode>()
      .on("start", (event, d) => {
        if (!event.active) {
          simulation.alphaTarget(0.3).restart();
        }
        d.fx = d.x;
        d.fy = d.y;
      })
      .on("drag", (event, d) => {
        d.fx = event.x;
        d.fy = event.y;
      })
      .on("end", (event, d) => {
        if (!event.active) {
          simulation.alphaTarget(0);
        }
        d.fx = null;
        d.fy = null;
      });

    const node = root
      .append("g")
      .selectAll("g")
      .data(simNodes)
      .join("g")
      .style("cursor", (d) => (d.isAttribute ? "default" : "pointer"))
      .style("opacity", (d) => {
        if (d.isAttribute) {
          return filteredIds.has(d.parentId ?? "") ? 0.98 : 0.16;
        }
        return filteredIds.has(d.id) ? 1 : 0.16;
      })
      .on("click", (_, d) => {
        if (d.isAttribute) {
          return;
        }
        onSelect(d);
      })
      .call((selection) => {
        (dragBehavior as any)(selection as any);
      });

    node
      .append("circle")
      .attr("r", (d) => d.size + 6)
      .attr("fill", "none")
      .attr("stroke", (d) => DOMAIN_COLOR[d.domain])
      .attr("stroke-opacity", (d) => (d.isAttribute ? 0 : 0.18));

    node
      .append("circle")
      .attr("r", (d) => d.size)
      .attr("fill", (d) => (d.isAttribute ? "#0f1b2b" : `${DOMAIN_COLOR[d.domain]}22`))
      .attr("stroke", (d) => {
        if (d.isAttribute) {
          return `${DOMAIN_COLOR[d.domain]}99`;
        }
        return d.id === selectedNodeId ? "#ffffff" : DOMAIN_COLOR[d.domain];
      })
      .attr("stroke-width", (d) => {
        if (d.isAttribute) {
          return 1;
        }
        return d.id === selectedNodeId ? 2.4 : 1.5;
      });

    node
      .append("text")
      .text((d) => d.label)
      .attr("text-anchor", "middle")
      .attr("dy", (d) => (d.isAttribute ? 3 : -3))
      .attr("fill", (d) => DOMAIN_COLOR[d.domain])
      .attr("font-size", (d) => (d.isAttribute ? 8.5 : 12))
      .attr("font-weight", (d) => (d.isAttribute ? 500 : 700));

    node
      .append("text")
      .text((d) => d.en)
      .attr("text-anchor", "middle")
      .attr("dy", 12)
      .attr("fill", (d) => DOMAIN_COLOR[d.domain])
      .attr("opacity", 0.66)
      .attr("font-size", 9);
    node
      .selectAll("text")
      .filter((d: unknown) => Boolean((d as ExtendedNode).isAttribute))
      .filter((_, i) => i % 2 === 1)
      .remove();

    simulation.on("tick", () => {
      link.attr("d", (d) => {
        const source = d.source as SimNode;
        const target = d.target as SimNode;
        if (!source || !target || typeof d.source === "string" || typeof d.target === "string") {
          return "";
        }
        if (source.id === target.id) {
          const x = source.x ?? 0;
          const y = source.y ?? 0;
          return `M${x},${y - 20} C${x + 60},${y - 80} ${x + 80},${y + 20} ${x},${y + 20}`;
        }
        const sx = source.x ?? 0;
        const sy = source.y ?? 0;
        const tx = target.x ?? 0;
        const ty = target.y ?? 0;
        const mx = (sx + tx) / 2 - (ty - sy) * 0.12;
        const my = (sy + ty) / 2 + (tx - sx) * 0.12;
        return `M${sx},${sy} Q${mx},${my} ${tx},${ty}`;
      });
      linkLabels.attr("x", (d) => {
        const source = d.source as SimNode;
        const target = d.target as SimNode;
        if (!source || !target || typeof d.source === "string" || typeof d.target === "string") {
          return 0;
        }
        return ((source.x ?? 0) + (target.x ?? 0)) / 2;
      });
      linkLabels.attr("y", (d) => {
        const source = d.source as SimNode;
        const target = d.target as SimNode;
        if (!source || !target || typeof d.source === "string" || typeof d.target === "string") {
          return 0;
        }
        return ((source.y ?? 0) + (target.y ?? 0)) / 2 - 6;
      });
      node.attr("transform", (d) => `translate(${d.x ?? 0},${d.y ?? 0})`);
    });

    return () => {
      simulation.stop();
    };
  }, [activeDomains, filteredIds, links, nodes, onSelect, search, selectedNodeId]);

  return <svg ref={svgRef} className="graph-svg" />;
}
