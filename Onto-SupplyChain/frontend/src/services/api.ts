import type { ATPResponse, GraphLink, GraphNode, ScenarioItem } from "../types";

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:5000/api").replace(/\/$/, "");

export async function fetchGraph(): Promise<{ nodes: GraphNode[]; links: GraphLink[] }> {
  const response = await fetch(`${API_BASE}/ontology/graph`);
  if (!response.ok) {
    throw new Error("图谱数据加载失败");
  }
  return response.json();
}

export async function fetchScenarios(): Promise<ScenarioItem[]> {
  const response = await fetch(`${API_BASE}/scenarios`);
  if (!response.ok) {
    throw new Error("场景数据加载失败");
  }
  const data = await response.json();
  return data.items;
}

export async function runScenario(scenarioCode: string, message?: string): Promise<ATPResponse> {
  const response = await fetch(`${API_BASE}/scenarios/${scenarioCode}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  if (!response.ok) {
    throw new Error("场景执行失败");
  }
  return response.json();
}

export async function sendChat(message: string, scenarioCode?: string): Promise<ATPResponse> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, scenario_code: scenarioCode }),
  });
  if (!response.ok) {
    throw new Error("对话请求失败");
  }
  return response.json();
}

export async function fetchHealth(): Promise<{ deepseek_configured: boolean; database_ready: boolean }> {
  const response = await fetch(`${API_BASE}/health`);
  if (!response.ok) {
    throw new Error("健康检查失败");
  }
  return response.json();
}
