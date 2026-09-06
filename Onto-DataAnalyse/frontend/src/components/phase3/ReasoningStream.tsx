import { useEffect, useRef } from 'react';
import type { ExecutionStep } from '../../types/scenario';
import styles from './ReasoningStream.module.css';

interface Props {
  step: ExecutionStep;
}

/**
 * AI 推理流式展示 — 渲染思维链（流式打字机效果 + 完成后展开结论和建议）
 */
export default function ReasoningStream({ step }: Props) {
  const thinkRef = useRef<HTMLDivElement>(null);

  // 流式接收时滚到底
  useEffect(() => {
    if (thinkRef.current) {
      thinkRef.current.scrollTop = thinkRef.current.scrollHeight;
    }
  }, [step.thinking_buffer]);

  const isStreaming = step.status === 'running' && !step.thinking;
  const thinkText = step.thinking ?? extractTag(step.thinking_buffer ?? '', 'thinking') ?? step.thinking_buffer ?? '';

  return (
    <div className={styles.wrap}>
      <div className={styles.head}>
        <span className={styles.aiBadge}>
          <span className={styles.aiDot} />
          AI 推理 · {step.description}
        </span>
        {step.confidence && (
          <span className={styles.confidence}>
            平均置信度 <b>{step.confidence.avg}%</b>
          </span>
        )}
      </div>

      {/* 思维链 */}
      {thinkText && (
        <div className={styles.section}>
          <div className={styles.sectionTitle}>
            <span className={styles.spinner} style={{ opacity: isStreaming ? 1 : 0 }} />
            思维链 {isStreaming && '（推理中...）'}
          </div>
          <div className={styles.think} ref={thinkRef}>
            {thinkText.split('\n').map((line, i) => (
              <div key={i} className={styles.thinkLine}>{line}</div>
            ))}
            {isStreaming && <span className={styles.cursor}>▊</span>}
          </div>
        </div>
      )}

      {/* 结论 */}
      {step.conclusion && (
        <div className={`${styles.section} ${styles.conclusion}`}>
          <div className={styles.sectionTitle}>📊 推理结论</div>
          <FormattedBlock text={step.conclusion} />
        </div>
      )}

      {/* 建议 */}
      {step.recommendations && (
        <div className={`${styles.section} ${styles.recommendations}`}>
          <div className={styles.sectionTitle}>🎯 行动建议</div>
          <FormattedBlock text={step.recommendations} />
        </div>
      )}
    </div>
  );
}

function FormattedBlock({ text }: { text: string }) {
  // 简单的 Markdown-ish 渲染（行内 **bold** + 段落）
  return (
    <div className={styles.formatted}>
      {text.split('\n').map((line, i) => (
        <div key={i} className={styles.formattedLine} dangerouslySetInnerHTML={{ __html: formatLine(line) }} />
      ))}
    </div>
  );
}

function formatLine(line: string): string {
  let escaped = line.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  escaped = escaped.replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>');
  // 高亮 [P0/P1/P2]
  escaped = escaped.replace(/\[(P0)\]/g, '<span class="priorityHigh">[P0]</span>');
  escaped = escaped.replace(/\[(P1)\]/g, '<span class="priorityMid">[P1]</span>');
  escaped = escaped.replace(/\[(P2)\]/g, '<span class="priorityLow">[P2]</span>');
  // 置信度标签
  escaped = escaped.replace(/\[置信度:\s*(\d+)%\]/g, '<span class="confTag">置信度 $1%</span>');
  return escaped;
}

function extractTag(text: string, tag: string): string | null {
  const m = text.match(new RegExp(`<${tag}>([\\s\\S]*?)(</${tag}>|$)`));
  return m ? m[1].trim() : null;
}
