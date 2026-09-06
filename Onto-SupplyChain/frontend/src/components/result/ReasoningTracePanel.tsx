import type { ATPResponse, GraphNode } from "../../types";

interface Props {
  data?: ATPResponse;
  selectedNode?: GraphNode;
}

export function ReasoningTracePanel({ data, selectedNode }: Props) {
  const trace = data?.scenario_result.reasoning_trace ?? [];

  return (
    <section className="trace-panel">
      <div className="trace-header">
        <div>
          <h2>AI 推理过程面板</h2>
          <p>记录本体对象查询、规则命中、ATP 方案比较与最终承诺生成全过程</p>
        </div>
        <div className="trace-context">
          {selectedNode ? `当前图谱焦点：${selectedNode.label} / ${selectedNode.en}` : "当前图谱焦点：全局"}
        </div>
      </div>

      <div className="trace-body">
        {!trace.length ? (
          <div className="trace-empty">运行任一场景后，这里会显示详细推理步骤、对象数据查询记录和本体规则应用过程。</div>
        ) : (
          trace.map((item) => (
            <article key={item.step} className="trace-step">
              <div className="trace-step-top">
                <span className="trace-step-id">{item.step}</span>
                <strong>{item.title}</strong>
              </div>
              <ul>
                {item.details.map((detail) => (
                  <li key={detail}>{detail}</li>
                ))}
              </ul>
              <div className="trace-meta">
                <div className="trace-meta-row">
                  <span>规则</span>
                  <div className="trace-tags">
                    {item.rule_ids.map((rule) => (
                      <em key={rule}>{rule}</em>
                    ))}
                  </div>
                </div>
                <div className="trace-meta-row">
                  <span>对象</span>
                  <div className="trace-tags">
                    {item.objects.map((objectId) => (
                      <em key={objectId}>{objectId}</em>
                    ))}
                  </div>
                </div>
              </div>
            </article>
          ))
        )}
      </div>
    </section>
  );
}
