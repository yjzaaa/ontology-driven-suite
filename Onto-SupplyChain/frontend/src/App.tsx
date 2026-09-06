import { useEffect, useState } from "react";
import "./styles.css";
import { ChatPanel } from "./components/chat/ChatPanel";
import { OntologyGraph } from "./components/graph/OntologyGraph";
import { ATPResultPanel } from "./components/result/ATPResultPanel";
import { ReasoningTracePanel } from "./components/result/ReasoningTracePanel";
import { fetchGraph, fetchHealth, fetchScenarios, runScenario, sendChat } from "./services/api";
import type { ATPResponse, ChatMessage, GraphLink, GraphNode, ScenarioItem } from "./types";

const DOMAIN_OPTIONS = [
  { code: "demand", label: "需求域" },
  { code: "production", label: "生产域" },
  { code: "supply", label: "供应域" },
  { code: "planning", label: "计划域" },
];

export default function App() {
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [links, setLinks] = useState<GraphLink[]>([]);
  const [scenarios, setScenarios] = useState<ScenarioItem[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([
    { id: "sys-1", role: "system", content: "选择预设场景后，系统会自动完成库存、BOM、供应与产能分析，并生成 ATP 承诺说明。" },
  ]);
  const [search, setSearch] = useState("");
  const [activeDomains, setActiveDomains] = useState<string[]>(DOMAIN_OPTIONS.map((item) => item.code));
  const [selectedNode, setSelectedNode] = useState<GraphNode | undefined>();
  const [activeScenarioCode, setActiveScenarioCode] = useState<string>();
  const [latestResponse, setLatestResponse] = useState<ATPResponse>();
  const [loading, setLoading] = useState(false);
  const [health, setHealth] = useState<{ deepseek_configured: boolean; database_ready: boolean } | null>(null);

  useEffect(() => {
    Promise.all([fetchGraph(), fetchScenarios(), fetchHealth()]).then(([graph, items, healthData]) => {
      setNodes(graph.nodes);
      setLinks(graph.links);
      setScenarios(items);
      setHealth(healthData);
    });
  }, []);

  async function handleRunScenario(scenarioCode: string) {
    const scenario = scenarios.find((item) => item.scenario_code === scenarioCode);
    if (!scenario) {
      return;
    }
    setActiveScenarioCode(scenarioCode);
    setMessages((current) => [...current, { id: `user-${Date.now()}`, role: "user", content: scenario.user_prompt }]);
    setLoading(true);
    try {
      const response = await runScenario(scenarioCode, scenario.user_prompt);
      setLatestResponse(response);
      setMessages((current) => [
        ...current,
        { id: `assistant-${Date.now()}`, role: "assistant", content: response.assistant.user_facing_reply },
      ]);
    } finally {
      setLoading(false);
    }
  }

  async function handleSend(message: string) {
    setMessages((current) => [...current, { id: `user-${Date.now()}`, role: "user", content: message }]);
    setLoading(true);
    try {
      const response = await sendChat(message, activeScenarioCode);
      setLatestResponse(response);
      setMessages((current) => [
        ...current,
        { id: `assistant-${Date.now()}`, role: "assistant", content: response.assistant.user_facing_reply },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <div className="title-row">
            <span className="logo-mark">ATP</span>
            <div>
              <h1>供应链本体模型 + AI 驱动 ATP 交期承诺演示</h1>
              <p>SQLite · Flask · React · DeepSeek</p>
            </div>
          </div>
        </div>
        <div className="status-strip">
          <span className={health?.database_ready ? "ok" : ""}>数据库 {health?.database_ready ? "已就绪" : "未就绪"}</span>
          <span className={health?.deepseek_configured ? "ok" : "warn"}>大模型 {health?.deepseek_configured ? "已配置" : "未配置，当前走回退模式"}</span>
        </div>
      </header>

      <main className="workspace">
        <section className="left-column">
          <section className="graph-panel">
            <div className="graph-toolbar">
              <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="搜索实体..." />
              <div className="domain-filters">
                {DOMAIN_OPTIONS.map((item) => {
                  const active = activeDomains.includes(item.code);
                  return (
                    <button
                      key={item.code}
                      className={active ? "active" : ""}
                      onClick={() =>
                        setActiveDomains((current) =>
                          active ? current.filter((code) => code !== item.code) : [...current, item.code],
                        )
                      }
                    >
                      {item.label}
                    </button>
                  );
                })}
              </div>
            </div>
            <div className="graph-frame">
              <OntologyGraph
                nodes={nodes}
                links={links}
                selectedNodeId={selectedNode?.id}
                search={search}
                activeDomains={activeDomains}
                onSelect={setSelectedNode}
              />
            </div>
          </section>
          <ReasoningTracePanel data={latestResponse} selectedNode={selectedNode} />
        </section>

        <section className="right-panel">
          <ChatPanel
            scenarios={scenarios}
            activeScenarioCode={activeScenarioCode}
            selectedNodeLabel={selectedNode ? `${selectedNode.label} / ${selectedNode.en}` : undefined}
            messages={messages}
            loading={loading}
            suggestedQuestions={latestResponse?.assistant.follow_up_questions ?? []}
            onRunScenario={handleRunScenario}
            onSend={handleSend}
          />
          <ATPResultPanel data={latestResponse} />
        </section>
      </main>
    </div>
  );
}
