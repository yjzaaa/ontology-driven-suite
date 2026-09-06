import { useEffect, useState } from 'react';
import styles from './YamlViewer.module.css';

interface Props {
  yamlText: string;
  filename?: string;
}

/** 简单的 YAML 高亮：键名 / 字符串 / 注释 / 数字 / 布尔 */
function highlight(line: string): { html: string } {
  let s = line
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
  // 注释
  if (/^\s*#/.test(s)) {
    return { html: `<span class="${styles.tComment}">${s}</span>` };
  }
  // 列表项前缀
  s = s.replace(/^(\s*-\s)/, `<span class="${styles.tDash}">$1</span>`);
  // key:
  s = s.replace(/^(\s*)([A-Za-z_][\w-]*)(\s*:)/, (_m, sp, key, colon) =>
    `${sp}<span class="${styles.tKey}">${key}</span>${colon}`,
  );
  // 字符串值（单/双引号）
  s = s.replace(/(['"])([^'"]*?)\1/g, `<span class="${styles.tString}">$1$2$1</span>`);
  // 数字与布尔
  s = s.replace(/(\s)(\d+\.?\d*)(\s|$)/g, `$1<span class="${styles.tNum}">$2</span>$3`);
  s = s.replace(/\b(true|false|null)\b/g, `<span class="${styles.tBool}">$1</span>`);
  return { html: s };
}

export default function YamlViewer({ yamlText, filename }: Props) {
  const [lines, setLines] = useState<string[]>([]);
  useEffect(() => {
    setLines((yamlText || '').split('\n'));
  }, [yamlText]);

  return (
    <div className={styles.box}>
      {filename && <div className={styles.filename}>{filename}</div>}
      <pre className={styles.code}>
        <code>
          {lines.map((line, i) => (
            <div key={i} className={styles.line}>
              <span className={styles.lineNo}>{i + 1}</span>
              <span
                className={styles.content}
                dangerouslySetInnerHTML={{ __html: highlight(line).html || '&nbsp;' }}
              />
            </div>
          ))}
        </code>
      </pre>
    </div>
  );
}
