import { useState } from "react";
import type { ChatMessage, ScenarioItem } from "../../types";

interface Props {
  scenarios: ScenarioItem[];
  activeScenarioCode?: string;
  selectedNodeLabel?: string;
  messages: ChatMessage[];
  loading: boolean;
  suggestedQuestions: string[];
  onRunScenario: (scenarioCode: string) => void;
  onSend: (message: string) => void;
}

export function ChatPanel({
  scenarios,
  activeScenarioCode,
  selectedNodeLabel,
  messages,
  loading,
  suggestedQuestions,
  onRunScenario,
  onSend,
}: Props) {
  const [draft, setDraft] = useState("");

  return (
    <section className="chat-panel">
      <div className="chat-top">
        <div className="panel-title-row">
          <div>
            <h2>AI ATP Copilot</h2>
            <p>预设场景驱动交期承诺推演与业务解释</p>
          </div>
          <div className="context-badge">{selectedNodeLabel ? `当前关注：${selectedNodeLabel}` : "当前关注：全局ATP"}</div>
        </div>
        <div className="scenario-grid">
          {scenarios.map((scenario) => (
            <button
              key={scenario.scenario_code}
              className={`scenario-card ${activeScenarioCode === scenario.scenario_code ? "active" : ""}`}
              onClick={() => onRunScenario(scenario.scenario_code)}
            >
              <span>{scenario.scenario_name}</span>
              <small>{scenario.user_prompt}</small>
            </button>
          ))}
        </div>
      </div>

      <div className="messages">
        {messages.map((message) => (
          <div key={message.id} className={`message ${message.role}`}>
            <div className="message-role">{message.role === "assistant" ? "AI" : message.role === "user" ? "你" : "系统"}</div>
            <div className="message-content">{message.content}</div>
          </div>
        ))}
        {loading ? <div className="message assistant"><div className="message-role">AI</div><div className="message-content">正在计算库存、BOM、产能和ATP方案...</div></div> : null}
      </div>

      {suggestedQuestions.length ? (
        <div className="suggested-area">
          {suggestedQuestions.map((question) => (
            <button key={question} className="suggest-btn" onClick={() => onSend(question)}>
              {question}
            </button>
          ))}
        </div>
      ) : null}

      <form
        className="chat-input-row"
        onSubmit={(event) => {
          event.preventDefault();
          if (!draft.trim()) {
            return;
          }
          onSend(draft.trim());
          setDraft("");
        }}
      >
        <input value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="继续追问：如果允许加班呢？" />
        <button type="submit">发送</button>
      </form>
    </section>
  );
}
