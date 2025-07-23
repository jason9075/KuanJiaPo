const puppeteer = require('puppeteer');

let browser; // 用外層變數存 browser 讓 signal handler 能關閉它

(async () => {
  browser = await puppeteer.launch({
    executablePath: '/home/jason9075/.nix-profile/bin/chromium',
    headless: false,
    args: [
      '--no-sandbox',
      '--use-fake-ui-for-media-stream',
      '--autoplay-policy=no-user-gesture-required',
      '--start-maximized',
      '--ignore-certificate-errors',
    ]
  });

  const page = await browser.newPage();

  await page.goto('https://localhost:8000?autocall=true', {
    waitUntil: 'networkidle2',
  });

  console.log('✅ WebRTC client joined');
})();

// Graceful shutdown handler
const shutdown = async (signal) => {
  console.log(`\nReceived ${signal}, closing browser...`);
  try {
    if (browser) await browser.close();
  } catch (err) {
    console.error('Error closing browser:', err);
  } finally {
    process.exit(0);
  }
};

process.on('SIGINT', () => shutdown('SIGINT'));
process.on('SIGTERM', () => shutdown('SIGTERM'));

