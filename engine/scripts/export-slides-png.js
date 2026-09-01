#!/usr/bin/env node
// Screenshot each slide to PNG for PDF export. Mirrors how engine/html2pptx.js
// loads and sizes a slide page (file:// + computed body dimensions) so the
// exported PDF matches the PPTX build's layout. Does not modify build.js or
// html2pptx.js.
//
// Usage: node export-slides-png.js <projectName> <version> <outDir>

const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT_DIR = path.join(__dirname, '..');
const PROJECTS_DIR = path.join(ROOT_DIR, 'projects');

function naturalSlideSort(a, b) {
  const na = parseInt((a.match(/slide(\d+)/) || [])[1] || '0', 10);
  const nb = parseInt((b.match(/slide(\d+)/) || [])[1] || '0', 10);
  return na - nb;
}

async function main() {
  const [projectName, version, outDir] = process.argv.slice(2);
  if (!projectName || !version || !outDir) {
    console.error('Usage: node export-slides-png.js <projectName> <version> <outDir>');
    process.exit(1);
  }

  const htmlDir = path.join(PROJECTS_DIR, projectName, version, 'html');
  if (!fs.existsSync(htmlDir)) {
    console.error(`Project html dir not found: ${htmlDir}`);
    process.exit(1);
  }
  fs.mkdirSync(outDir, { recursive: true });

  const files = fs.readdirSync(htmlDir)
    .filter((f) => f.endsWith('.html') && !f.includes('.backup.'))
    .sort(naturalSlideSort);

  if (files.length === 0) {
    console.error('No slide HTML files found.');
    process.exit(1);
  }

  const browser = await chromium.launch();
  try {
    for (let i = 0; i < files.length; i++) {
      const filePath = path.join(htmlDir, files[i]);
      const page = await browser.newPage({ deviceScaleFactor: 2 });
      await page.goto(`file://${filePath}`);

      const bodyDimensions = await page.evaluate(() => {
        const rect = document.body.getBoundingClientRect();
        return { width: rect.width, height: rect.height };
      });
      await page.setViewportSize({
        width: Math.round(bodyDimensions.width),
        height: Math.round(bodyDimensions.height),
      });

      const outPath = path.join(outDir, `${String(i + 1).padStart(3, '0')}.png`);
      await page.screenshot({ path: outPath });
      await page.close();
      console.log(`(${i + 1}/${files.length}) ${files[i]} -> ${path.basename(outPath)}`);
    }
  } finally {
    await browser.close();
  }
}

main().catch((err) => {
  console.error(err.message);
  process.exit(1);
});
