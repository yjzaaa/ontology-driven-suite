import { useRef, useState, type DragEvent, type ChangeEvent } from 'react';
import { phase1Api } from '../../api/phase1Api';
import styles from './FileUploadCard.module.css';

interface Props {
  title: string;
  hint: string;
  demoFileName: string;             // 用于"下载示例"按钮
  value: string;
  onChange: (text: string, filename?: string) => void;
}

export default function FileUploadCard({ title, hint, demoFileName, value, onChange }: Props) {
  const [dragOver, setDragOver] = useState(false);
  const [filename, setFilename] = useState<string>('');
  const [error, setError] = useState<string>('');
  const inputRef = useRef<HTMLInputElement>(null);

  const readFile = (file: File) => {
    if (!/\.(md|txt|markdown)$/i.test(file.name)) {
      setError('仅支持 .md / .txt / .markdown 文件');
      return;
    }
    if (file.size > 200 * 1024) {
      setError('文件大小超过 200KB');
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      setError('');
      setFilename(file.name);
      onChange(String(reader.result ?? ''), file.name);
    };
    reader.onerror = () => setError('读取文件失败');
    reader.readAsText(file, 'utf-8');
  };

  const onDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files?.[0];
    if (f) readFile(f);
  };

  const onPick = (e: ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) readFile(f);
  };

  const downloadDemo = async () => {
    try {
      const text = await phase1Api.downloadDemoFile(demoFileName);
      setFilename(demoFileName);
      setError('');
      onChange(text, demoFileName);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const clear = () => {
    setFilename('');
    onChange('', undefined);
  };

  return (
    <div className={styles.card}>
      <div className={styles.head}>
        <div>
          <div className={styles.title}>{title}</div>
          <div className={styles.hint}>{hint}</div>
        </div>
        <button className="btn-secondary" onClick={downloadDemo} type="button">
          下载示例
        </button>
      </div>

      {!value ? (
        <div
          className={`${styles.dropZone} ${dragOver ? styles.dragOver : ''}`}
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
        >
          <div className={styles.dropIcon}>📄</div>
          <div className={styles.dropText}>
            拖拽 <code>.md</code> 或 <code>.txt</code> 文件到此处<br />
            或点击选择文件
          </div>
          <div className={styles.dropTextSub}>
            或者点右上角「下载示例」直接载入演示文件
          </div>
          <input
            ref={inputRef}
            type="file"
            accept=".md,.txt,.markdown"
            style={{ display: 'none' }}
            onChange={onPick}
          />
        </div>
      ) : (
        <div className={styles.loaded}>
          <div className={styles.fileInfo}>
            <span className={styles.fileIcon}>✓</span>
            <span className={styles.fileName}>{filename || '已加载'}</span>
            <span className={styles.fileSize}>{value.length.toLocaleString()} 字符</span>
          </div>
          <button className={styles.removeBtn} onClick={clear} type="button">
            ✕ 清除
          </button>
        </div>
      )}

      {error && <div className={styles.error}>{error}</div>}
    </div>
  );
}
