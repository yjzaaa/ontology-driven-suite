import puppeteer from 'puppeteer-core';
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const browser = await puppeteer.launch({ executablePath: CHROME, headless: true });
const page = await browser.newPage();
await page.setViewport({ width: 1500, height: 950 });
const errs = [];
page.on('pageerror', e => errs.push('pageerror: ' + e.message));
await page.goto('http://127.0.0.1:3080/', { waitUntil: 'domcontentloaded', timeout: 20000 });
await new Promise(r => setTimeout(r, 5000));
const info = await page.evaluate(() => {
  const t = document.body.innerText;
  return {
    title: document.title,
    sample: t.slice(0, 250).replace(/\n+/g, ' | '),
  };
});
console.log('页面:', JSON.stringify(info, null, 2));
await page.screenshot({ path: 'dsh_home.png' });
console.log('errors:', errs.length ? errs.join('\n') : '(none)');
await browser.close();
