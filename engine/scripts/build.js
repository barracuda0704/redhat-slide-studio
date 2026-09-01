#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const pptxgen = require('pptxgenjs');
const html2pptx = require('../engine/html2pptx');
const { detectProjectType, loadProjectMeta, saveProjectMeta } = require('./lib/project-meta');

const ROOT_DIR = path.join(__dirname, '..');
const PROJECTS_DIR = path.join(ROOT_DIR, 'projects');

const SLIDE_NOTES_REGEX = /\*\*.*Notes:\*\*([\s\S]*?)(?=\n---|\n## Slide |\Z)/m;

function parseNotesFromContent(contentPath) {
  if (!fs.existsSync(contentPath)) return {};
  const text = fs.readFileSync(contentPath, 'utf-8');
  const slideRegex = /^## Slide (\d+):/gm;
  const positions = [];
  let match;
  while ((match = slideRegex.exec(text)) !== null) {
    positions.push({ num: parseInt(match[1], 10), start: match.index });
  }
  const notes = {};
  for (let i = 0; i < positions.length; i++) {
    const slideText = text.slice(
      positions[i].start,
      positions[i + 1]?.start || text.length
    );
    const notesMatch = slideText.match(SLIDE_NOTES_REGEX);
    if (notesMatch) {
      const noteLines = notesMatch[1]
        .split('\n')
        .map((l) => l.replace(/^\s*-\s*/, '').trim())
        .filter((l) => l.length > 0);
      notes[positions[i].num] = noteLines.join('\n');
    }
  }
  return notes;
}

function todayIso() {
  return new Date().toISOString().split('T')[0];
}

function parseArgs(argv) {
  const args = argv.slice(2);
  const flags = {};
  const positional = [];
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    if (a === '--all' || a === '--merge') {
      flags[a.slice(2)] = true;
    } else if (a.startsWith('--')) {
      const key = a.slice(2);
      const next = args[i + 1];
      if (next === undefined || next.startsWith('--')) {
        flags[key] = true;
      } else {
        flags[key] = next;
        i++;
      }
    } else {
      positional.push(a);
    }
  }
  return { flags, positional };
}

function isVersionLabel(s) {
  return typeof s === 'string' && /^v\d/.test(s);
}

function readDirSafe(dir) {
  try {
    return fs.readdirSync(dir, { withFileTypes: true });
  } catch {
    return [];
  }
}

function listVersionDirs(parent) {
  return readDirSafe(parent)
    .filter((d) => d.isDirectory() && /^v\d/.test(d.name))
    .map((d) => d.name)
    .sort();
}

function listModuleDirs(projectRoot) {
  return readDirSafe(projectRoot)
    .filter(
      (d) =>
        d.isDirectory() &&
        !d.name.startsWith('.') &&
        d.name !== 'output' &&
        fs.existsSync(path.join(projectRoot, d.name, 'module.json'))
    )
    .map((d) => d.name)
    .sort();
}

function listLegacyChapterDirs(projectRoot) {
  return readDirSafe(projectRoot)
    .filter((d) => d.isDirectory() && /^chapter-\d+$/.test(d.name))
    .map((d) => d.name)
    .sort();
}

function readJsonSafe(filePath) {
  try {
    return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
  } catch {
    return null;
  }
}

function loadProjectInfo(versionPath, fallbackTitle) {
  const projectJsonPath = path.join(versionPath, 'project.json');
  const data = readJsonSafe(projectJsonPath);
  if (data) return { title: data.title || fallbackTitle, author: data.author || 'Red Hat Korea', _path: projectJsonPath, _data: data };
  return { title: fallbackTitle, author: 'Red Hat Korea', _path: projectJsonPath, _data: null };
}

async function renderSlidesIntoPptx({ pptx, htmlDir, contentPath, label }) {
  const htmlFiles = readDirSafe(htmlDir)
    .filter((d) => d.isFile() && d.name.endsWith('.html') && d.name.startsWith('slide'))
    .map((d) => d.name)
    .sort((a, b) => {
      const na = parseInt(a.match(/slide(\d+)/)?.[1] || '0', 10);
      const nb = parseInt(b.match(/slide(\d+)/)?.[1] || '0', 10);
      return na - nb;
    });

  if (htmlFiles.length === 0) {
    console.log(`⚠️  No HTML files found in ${htmlDir}, skipping.`);
    return { successCount: 0, errorCount: 0 };
  }

  console.log(`\n📖 ${label} (${htmlFiles.length} slides)`);
  const slideNotes = parseNotesFromContent(contentPath);
  if (Object.keys(slideNotes).length > 0) {
    console.log(`   Found ${Object.keys(slideNotes).length} slide notes`);
  }

  let successCount = 0;
  let errorCount = 0;
  for (let i = 0; i < htmlFiles.length; i++) {
    const file = htmlFiles[i];
    process.stdout.write(`   (${i + 1}/${htmlFiles.length}) ${file}`);
    try {
      const result = await html2pptx(path.join(htmlDir, file), pptx);
      const slideNum = i + 1;
      const fileNumMatch = file.match(/^slide(\d+)/);
      const fileNum = fileNumMatch ? parseInt(fileNumMatch[1], 10) : slideNum;
      const note = slideNotes[slideNum] || slideNotes[fileNum];
      if (note && result?.slide) {
        result.slide.addNotes(note);
        process.stdout.write(' [+notes]');
      }
      console.log(' ✓');
      successCount++;
    } catch (err) {
      console.log(` ✗ ${err.message}`);
      errorCount++;
    }
  }
  return { successCount, errorCount };
}

async function buildStandardVersion({ projectName, projectRoot, version }) {
  let resolved = version;
  if (resolved === 'latest' || !resolved) {
    const latestLink = path.join(projectRoot, 'latest');
    if (fs.existsSync(latestLink)) {
      resolved = fs.readlinkSync(latestLink);
    } else {
      const all = listVersionDirs(projectRoot);
      resolved = all[all.length - 1];
    }
  }
  if (!resolved) throw new Error(`No version found in "${projectName}".`);

  const versionPath = path.join(projectRoot, resolved);
  if (!fs.existsSync(versionPath)) {
    throw new Error(`Version "${resolved}" not found in "${projectName}".`);
  }

  const htmlDir = path.join(versionPath, 'html');
  const contentPath = path.join(versionPath, 'content.md');
  const info = loadProjectInfo(versionPath, projectName);

  console.log(`\n🔨 Building: ${projectName}/${resolved}`);
  console.log('─'.repeat(60));

  const pptx = new pptxgen();
  pptx.layout = 'LAYOUT_16x9';
  pptx.title = info.title;
  pptx.author = info.author;

  const result = await renderSlidesIntoPptx({
    pptx,
    htmlDir,
    contentPath,
    label: `${projectName}/${resolved}`,
  });

  const outputPath = path.join(versionPath, 'slides.pptx');
  await pptx.writeFile({ fileName: outputPath });

  if (info._data) {
    info._data.slides = result.successCount;
    info._data.updated = todayIso();
    if (result.errorCount === 0) info._data.status = 'final';
    fs.writeFileSync(info._path, JSON.stringify(info._data, null, 2) + '\n');
  }

  console.log('─'.repeat(60));
  console.log(`✅ Build complete: ${result.successCount} success, ${result.errorCount} errors`);
  console.log(`   Output: projects/${projectName}/${resolved}/slides.pptx\n`);
  return result;
}

function resolveModuleVersion(moduleRoot, version) {
  if (version && version !== 'latest') {
    const explicit = path.join(moduleRoot, version);
    if (!fs.existsSync(explicit)) {
      throw new Error(`Version "${version}" not found in module ${path.basename(moduleRoot)}.`);
    }
    return version;
  }
  const latestLink = path.join(moduleRoot, 'latest');
  if (fs.existsSync(latestLink)) {
    return fs.readlinkSync(latestLink);
  }
  const all = listVersionDirs(moduleRoot);
  if (all.length === 0) return null;
  return all[all.length - 1];
}

async function buildModule({
  projectName,
  projectRoot,
  moduleSlug,
  version,
  pptx,
  courseTitle,
  courseAuthor,
}) {
  const moduleRoot = path.join(projectRoot, moduleSlug);

  if (fs.existsSync(path.join(moduleRoot, 'module.json'))) {
    const versionLabel = resolveModuleVersion(moduleRoot, version);
    if (!versionLabel) {
      console.log(`⚠️  No versions in module "${moduleSlug}", skipping.`);
      return { successCount: 0, errorCount: 0 };
    }
    const versionPath = path.join(moduleRoot, versionLabel);
    const htmlDir = path.join(versionPath, 'html');
    const contentPath = path.join(versionPath, 'content.md');

    const moduleData = readJsonSafe(path.join(moduleRoot, 'module.json'));
    const moduleTitle = (moduleData && moduleData.title) || moduleSlug;

    const isStandalone = pptx === null;
    if (isStandalone) {
      pptx = new pptxgen();
      pptx.layout = 'LAYOUT_16x9';
      pptx.title = `${courseTitle} - ${moduleTitle}`;
      pptx.author = courseAuthor;
      console.log(`\n🔨 Building: ${projectName}/${moduleSlug}/${versionLabel}`);
      console.log('─'.repeat(60));
    }

    const result = await renderSlidesIntoPptx({
      pptx,
      htmlDir,
      contentPath,
      label: `${moduleSlug} (${versionLabel})`,
    });

    if (isStandalone) {
      const outputPath = path.join(versionPath, 'slides.pptx');
      await pptx.writeFile({ fileName: outputPath });
      console.log('─'.repeat(60));
      console.log(`✅ Build complete: ${result.successCount} success, ${result.errorCount} errors`);
      console.log(`   Output: projects/${projectName}/${moduleSlug}/${versionLabel}/slides.pptx\n`);
    }

    return result;
  }

  const legacyHtmlDir = path.join(moduleRoot, 'html');
  if (fs.existsSync(legacyHtmlDir)) {
    const contentPath = path.join(moduleRoot, 'content.md');
    const isStandalone = pptx === null;
    if (isStandalone) {
      pptx = new pptxgen();
      pptx.layout = 'LAYOUT_16x9';
      pptx.title = `${courseTitle} - ${moduleSlug}`;
      pptx.author = courseAuthor;
      console.log(`\n🔨 Building (legacy): ${projectName}/${moduleSlug}`);
      console.log('─'.repeat(60));
    }

    const result = await renderSlidesIntoPptx({
      pptx,
      htmlDir: legacyHtmlDir,
      contentPath,
      label: `${moduleSlug} (legacy)`,
    });

    if (isStandalone) {
      const outputPath = path.join(moduleRoot, 'slides.pptx');
      await pptx.writeFile({ fileName: outputPath });
      console.log('─'.repeat(60));
      console.log(
        `✅ Build complete: ${result.successCount} success, ${result.errorCount} errors`
      );
      console.log(`   Output: projects/${projectName}/${moduleSlug}/slides.pptx\n`);
    }
    return result;
  }

  throw new Error(
    `Module "${moduleSlug}" has neither module.json+v* nor legacy html/. Nothing to build.`
  );
}

async function buildAllModules({ projectName, projectRoot, merge }) {
  const { type: projectType, path: metaPath, data: courseData } = loadProjectMeta(projectRoot);
  const courseTitle = courseData.title || projectName;
  const courseAuthor = courseData.author || 'Red Hat Korea';

  let modules = listModuleDirs(projectRoot);
  if (modules.length === 0) {
    modules = listLegacyChapterDirs(projectRoot);
  }
  if (modules.length === 0) {
    throw new Error(`No modules or chapters found in course "${projectName}".`);
  }

  console.log(`\n🔨 Building ${projectType === 'workshop' ? 'workshop' : 'course'}: ${projectName} (${merge ? 'merged' : 'all modules'})`);
  console.log('─'.repeat(60));
  console.log(`Modules: ${modules.join(', ')}`);

  let totalSuccess = 0;
  let totalErrors = 0;

  if (merge) {
    const pptx = new pptxgen();
    pptx.layout = 'LAYOUT_16x9';
    pptx.title = courseTitle;
    pptx.author = courseAuthor;

    for (const moduleSlug of modules) {
      const r = await buildModule({
        projectName,
        projectRoot,
        moduleSlug,
        version: 'latest',
        pptx,
        courseTitle,
        courseAuthor,
      });
      totalSuccess += r.successCount;
      totalErrors += r.errorCount;
    }

    const outputDir = path.join(projectRoot, 'output');
    fs.mkdirSync(outputDir, { recursive: true });
    const outputPath = path.join(outputDir, 'full-course.pptx');
    await pptx.writeFile({ fileName: outputPath });

    console.log('\n' + '─'.repeat(60));
    console.log(`✅ Merge complete: ${totalSuccess} success, ${totalErrors} errors`);
    console.log(`   Output: projects/${projectName}/output/full-course.pptx\n`);
  } else {
    for (const moduleSlug of modules) {
      const r = await buildModule({
        projectName,
        projectRoot,
        moduleSlug,
        version: 'latest',
        pptx: null,
        courseTitle,
        courseAuthor,
      });
      totalSuccess += r.successCount;
      totalErrors += r.errorCount;
    }
    console.log('─'.repeat(60));
    console.log(`✅ All modules built: ${totalSuccess} success, ${totalErrors} errors\n`);
  }

  if (courseData) {
    saveProjectMeta(metaPath, courseData);
  }
}

const USAGE = `Usage:
  Standard project:
    node scripts/build.js <project> [version]

  Course (multi-module):
    node scripts/build.js <project> <module> [version]   # build one module
    node scripts/build.js <project> --all                # build all modules (separate)
    node scripts/build.js <project> --merge              # merge all modules

Examples:
  node scripts/build.js ai-assessment
  node scripts/build.js ai-assessment v1.0
  node scripts/build.js agent-md observability
  node scripts/build.js agent-md observability v1.1
  node scripts/build.js aiops --all
  node scripts/build.js aiops --merge
`;

async function main() {
  const { flags, positional } = parseArgs(process.argv);

  if (positional.length === 0) {
    console.log(USAGE);
    process.exit(1);
  }

  const projectName = positional[0];
  const projectRoot = path.join(PROJECTS_DIR, projectName);
  if (!fs.existsSync(projectRoot)) {
    console.error(`❌ Project "${projectName}" not found.`);
    process.exit(1);
  }

  const projectType = detectProjectType(projectRoot);

  try {
    if (projectType === 'course' || projectType === 'workshop') {
      if (flags.all || flags.merge) {
        await buildAllModules({
          projectName,
          projectRoot,
          merge: !!flags.merge,
        });
        return;
      }

      const second = positional[1];
      const third = positional[2];

      if (!second) {
        console.error(`❌ Course project requires module name or --all/--merge.`);
        const modules = listModuleDirs(projectRoot);
        const legacy = listLegacyChapterDirs(projectRoot);
        if (modules.length > 0) console.error(`   Modules: ${modules.join(', ')}`);
        if (legacy.length > 0) console.error(`   Legacy chapters: ${legacy.join(', ')}`);
        console.error(`   Try: npm run build -- ${projectName} <module>`);
        process.exit(1);
      }

      const { path: metaPath, data: courseData } = loadProjectMeta(projectRoot);
      const courseTitle = courseData.title || projectName;
      const courseAuthor = courseData.author || 'Red Hat Korea';

      await buildModule({
        projectName,
        projectRoot,
        moduleSlug: second,
        version: third,
        pptx: null,
        courseTitle,
        courseAuthor,
      });
    } else {
      const version = positional[1] || 'latest';
      await buildStandardVersion({ projectName, projectRoot, version });
    }
  } catch (err) {
    console.error(`❌ ${err.message}`);
    process.exit(1);
  }
}

main().catch((err) => {
  console.error('Build failed:', err);
  process.exit(1);
});
