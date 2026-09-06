import puppeteer from 'puppeteer-core';
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const browser = await puppeteer.launch({ executablePath: CHROME, headless: true });
const page = await browser.newPage();
await page.setViewport({ width: 1500, height: 950 });
await page.goto('http://127.0.0.1:3080/', { waitUntil: 'domcontentloaded', timeout: 20000 });
await new Promise(r => setTimeout(r, 4500));
// 点"选择模型"
const clicked = await page.evaluate(() => {
  const el = [...document.querySelectorAll('*')].find(e => e.children.length === 0 && e.textContent.trim() === '选择模型');
  if (el) { el.click(); return true }
  return false;
});
console.log('点击选择模型:', clicked);
await new Promise(r => setTimeout(r, 1500));
const models = await page.evaluate(() => {
  const items = [...document.querySelectorAll('*')].filter(e => e.children.length === 0 && /\bdeepseek|kimi|k3|v4|flash\b/i.test(e.textContent));
  return [...new Set(items.map(e => e.textContent.trim()))].slice(0, 20);
});
console.log('模型相关文本:', models.length ? models.join(' | ') : '(未找到，可能下拉未展开)');
// 截全图
await page.screenshot({ path: 'dsh_models.png' });
await browser.close();
