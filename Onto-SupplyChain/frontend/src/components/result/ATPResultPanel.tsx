import type { ATPResponse } from "../../types";

interface Props {
  data?: ATPResponse;
}

export function ATPResultPanel({ data }: Props) {
  if (!data) {
    return (
      <section className="result-panel">
        <div className="result-empty">执行任一预设场景后，这里会展示 ATP 承诺日期、风险、原因链和备选方案。</div>
      </section>
    );
  }

  const summary = data.scenario_result.atp_summary;
  const assistant = data.assistant;

  return (
    <section className="result-panel">
      <div className="result-cards">
        <article className="metric-card">
          <span>承诺日期</span>
          <strong>{assistant.recommended_date}</strong>
        </article>
        <article className="metric-card">
          <span>置信度</span>
          <strong>{assistant.confidence_score}</strong>
        </article>
        <article className="metric-card">
          <span>风险等级</span>
          <strong>{assistant.risk_level}</strong>
        </article>
        <article className="metric-card">
          <span>LLM模式</span>
          <strong>{assistant.llm_mode}</strong>
        </article>
      </div>

      <div className="result-grid">
        <article className="result-block">
          <h3>推荐说明</h3>
          <p>{assistant.user_facing_reply}</p>
        </article>

        <article className="result-block">
          <h3>关键摘要</h3>
          <ul>
            <li>目标数量：{summary.target_quantity}</li>
            <li>成品可用库存：{summary.available_finished_qty}</li>
            <li>需补生产量：{summary.required_production_qty}</li>
            <li>物料齐套日期：{summary.material_ready_date}</li>
          </ul>
        </article>

        <article className="result-block">
          <h3>原因链</h3>
          <ul>
            {assistant.reason_chain.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>

        <article className="result-block">
          <h3>影响对象</h3>
          <div className="impact-tags">
            {assistant.impact_objects.map((object, index) => (
              <span key={`${object.id}-${index}`} className="impact-tag">
                {object.type}:{object.label}
              </span>
            ))}
          </div>
        </article>

        <article className="result-block">
          <h3>备选方案</h3>
          <div className="alt-list">
            {assistant.alternatives.map((item) => (
              <div key={item.commitment_type} className="alt-card">
                <strong>{item.commitment_type}</strong>
                <span>{item.committed_date}</span>
                <span>置信度 {item.confidence_score}</span>
                <span>成本影响 {item.cost_impact}</span>
                <p>{item.summary}</p>
              </div>
            ))}
          </div>
        </article>

        <article className="result-block">
          <h3>短缺与供应风险</h3>
          <div className="risk-table">
            <div>短缺项：{summary.shortages.length}</div>
            <div>供应风险项：{summary.supplier_risks.length}</div>
            <div>瓶颈压力：{summary.standard_detail.bottleneck_pressure}</div>
          </div>
        </article>
      </div>
    </section>
  );
}
