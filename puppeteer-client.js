const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    executablePath: '/home/jason9075/.nix-profile/bin/chromium',
    headless: false,
    args: [
      '--no-sandbox',
      '--use-fake-ui-for-media-stream', // ⬅️ 自動允許麥克風（不彈框）
      '--autoplay-policy=no-user-gesture-required', // ⬅️ 自動播放
      '--start-maximized',
      '--ignore-certificate-errors',
    ]
  });

  const page = await browser.newPage();

  await page.goto('https://localhost:8000?autocall=true', {
    waitUntil: 'networkidle2',
  });

  console.log('WebRTC client joined');

  // 保持開啟連線
})();

