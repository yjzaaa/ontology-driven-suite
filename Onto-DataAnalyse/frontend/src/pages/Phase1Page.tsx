import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { phase1Api } from '../api/phase1Api';
import { sseRequest } from '../api/sseClient';
import FileUploadCard from '../components/phase1/FileUploadCard';
import MarkdownRenderer from '../components/shared/MarkdownRenderer';
import RequirementCards from '../components/phase1/RequirementCards';
import type { ParsedRequirement } from '../types/requirement';
import styles from './Phase1Page.module.css';

type Status = 'idle' | 'uploading' | 'analyzing' | 'done' | 'error';

export default function Phase1Page() {
  const navigate = useNavigate();
  const [dbSchema, setDbSchema] = useState('');
  const [requirement, setRequirement] = useState('');
  const [previewTab, setPreviewTab] = useState<'schema' | 'requirement'>('schema');
  const [status, setStatus] = useState<Status>('idle');
  const [streamText, setStreamText] = useState('');
  const [parsed, setParsed] = useState<ParsedRequirement | null>(null);
  const [error, setError] = useState('');
  const streamBoxRef = useRef<HTMLPreElement>(null);

  // 恢复上次状态
  useEffect(() => {
    (async () => {
      try {
        const state = await phase1Api.getState();
        if (state.parsed_requirement) {
          setParsed(state.parsed_requirement);
          setStatus('done');
        }
      } catch {
        /* 忽略 */
      }
    })();
  }, []);

  // 流式追加时自动滚到底部
  useEffect(() => {
    if (streamBoxRef.current) {
      streamBoxRef.current.scrollTop = streamBoxRef.current.scrollHeight;
    }
  }, [streamText]);

  const canAnalyze = dbSchema.length > 0 && requirement.length > 0 && status !== 'analyzing';

  const startAnalyze = useCallback(async () => {
    setError('');
    setStreamText('');
    setParsed(null);
    setStatus('uploading');

    try {
      await phase1Api.upload(dbSchema, requirement);
    } catch (err) {
      setStatus('error');
      setError(`上传失败：${(err as Error).message}`);
      return;
    }

    setStatus('analyzing');
    await sseRequest(
      '/api/phase1/analyze',
      { method: 'POST', body: {} },
      {
        onMessage: (msg) => {
          if (msg.type === 'delta') {
            setStreamText((t) => t + ((msg.delta as string) || ''));
          } else if (msg.type === 'parsed') {
            setParsed(msg.data as ParsedRequirement);
            setStatus('done');
          } else if (msg.type === 'error') {
            setStatus('error');
            setError((msg.message as string) || '解析失败');
          }
        },
        onError: (err) => {
          setStatus('error');
          setError(err.message);
        },
      },
    );
  }, [dbSchema, requirement]);

  const goToPhase2 = useCallback(async () => {
    try {
      await phase1Api.confirm();
      navigate('/phase2');
    } catch (err) {
      setError(`确认失败：${(err as Error).message}`);
    }
  }, [navigate]);

  return (
    <div className={styles.layout}>
      {/* 左列：上传 + 预览 */}
      <div className={styles.left}>
        <FileUploadCard
          title="① 数据库 Schema 文档"
          hint="描述数据库表结构、字段含义、表关系（.md / .txt）"
          demoFileName="ecommerce_db_schema.md"
          value={dbSchema}
          onChange={(t) => setDbSchema(t)}
        />
        <FileUploadCard
          title="② 分析需求文档"
          hint="描述你希望分析的业务目标、关注指标、关注点（.md / .txt）"
          demoFileName="analysis_requirement.md"
          value={requirement}
          onChange={(t) => setRequirement(t)}
        />

        {(dbSchema || requirement) && (
          <div className={styles.previewCard}>
            <div className={styles.tabs}>
              <button
                className={`${styles.tab} ${previewTab === 'schema' ? styles.tabActive : ''}`}
                onClick={() => setPreviewTab('schema')}
                disabled={!dbSchema}
              >
                Schema 预览
              </button>
              <button
                className={`${styles.tab} ${previewTab === 'requirement' ? styles.tabActive : ''}`}
                onClick={() => setPreviewTab('requirement')}
                disabled={!requirement}
              >
                需求文档预览
              </button>
            </div>
            <div className={styles.previewBody}>
              <MarkdownRenderer
                content={previewTab === 'schema' ? dbSchema : requirement}
              />
            </div>
          </div>
        )}
      </div>

      {/* 右列：AI 解析 */}
      <div className={styles.right}>
        <div className={styles.actionsBar}>
          <div className={styles.statusInfo}>
            {status === 'idle' && '上传两个文档后即可开始 AI 解析'}
            {status === 'uploading' && '⏳ 上传中...'}
            {status === 'analyzing' && '🤖 AI 正在解析需求...'}
            {status === 'done' && '✓ 需求已解析'}
            {status === 'error' && `❌ ${error}`}
          </div>
          <div className={styles.actionsBtns}>
            <button
              className="btn-primary"
              onClick={startAnalyze}
              disabled={!canAnalyze}
              type="button"
            >
              {status === 'done' ? '重新解析' : '开始 AI 解析'}
            </button>
            {parsed && (
              <button className="btn-primary" onClick={goToPhase2} type="button">
                确认需求 → 进入阶段二
              </button>
            )}
          </div>
        </div>

        {status === 'analyzing' && (
          <div className={styles.streamCard}>
            <div className={styles.streamHead}>AI 流式输出（原始 JSON）</div>
            <pre ref={streamBoxRef} className={styles.streamBody}>{streamText}</pre>
          </div>
        )}

        {status === 'error' && error && (
          <div className={styles.errorCard}>
            <div className={styles.errorTitle}>错误</div>
            <div>{error}</div>
            {streamText && (
              <details className={styles.errorDetails}>
                <summary>查看 AI 原始输出</summary>
                <pre>{streamText.slice(0, 4000)}</pre>
              </details>
            )}
          </div>
        )}

        {parsed && <RequirementCards data={parsed} />}

        {!parsed && status === 'idle' && (
          <div className={styles.placeholder}>
            <div className={styles.placeholderIcon}>🧭</div>
            <div className={styles.placeholderTitle}>等待开始 AI 解析</div>
            <div className={styles.placeholderText}>
              AI 将基于两份文档自动识别：
              <br />
              · 核心分析目标与优先级
              <br />
              · 涉及的业务数据对象及对应数据库表
              <br />
              · 核心指标定义与计算口径
              <br />
              · 需要进一步澄清的问题
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
