// Container metadata helper for course/workshop project types
const fs = require('fs');
const path = require('path');

const CONTAINER_TYPES = ['course', 'workshop'];

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
}

function detectProjectType(projectRoot) {
  if (!fs.existsSync(projectRoot)) return null;
  const basename = path.basename(projectRoot);
  const coursePath = path.join(projectRoot, 'course.json');
  const workshopPath = path.join(projectRoot, 'workshop.json');
  const hasCourse = fs.existsSync(coursePath);
  const hasWorkshop = fs.existsSync(workshopPath);

  if (hasCourse && hasWorkshop) {
    throw new Error(
      `Both course.json and workshop.json found in "${basename}". Project must have exactly one.`
    );
  }

  for (const containerType of CONTAINER_TYPES) {
    const metaPath = path.join(projectRoot, `${containerType}.json`);
    if (!fs.existsSync(metaPath)) continue;
    const meta = readJson(metaPath);
    if (meta.type !== containerType) {
      throw new Error(
        `Metadata mismatch in "${basename}": file=${containerType}.json but type=${meta.type}. Aborting.`
      );
    }
    return containerType;
  }

  if (
    fs.existsSync(path.join(projectRoot, 'latest', 'project.json')) ||
    fs.existsSync(path.join(projectRoot, 'v1.0', 'project.json'))
  ) {
    return 'standard';
  }

  return null;
}

function findStandardMetaPath(projectRoot) {
  const latestMeta = path.join(projectRoot, 'latest', 'project.json');
  if (fs.existsSync(latestMeta)) return latestMeta;
  const entries = fs.readdirSync(projectRoot).filter((entry) => entry.startsWith('v'));
  for (const entry of entries.sort()) {
    const candidate = path.join(projectRoot, entry, 'project.json');
    if (fs.existsSync(candidate)) return candidate;
  }
  return null;
}

function loadProjectMeta(projectRoot) {
  const projectType = detectProjectType(projectRoot);
  const basename = path.basename(projectRoot);
  if (projectType === null) {
    throw new Error(`Cannot determine project type for "${basename}"`);
  }
  if (projectType === 'standard') {
    const metaPath = findStandardMetaPath(projectRoot);
    return { type: 'standard', path: metaPath, data: readJson(metaPath) };
  }
  const metaPath = path.join(projectRoot, `${projectType}.json`);
  return { type: projectType, path: metaPath, data: readJson(metaPath) };
}

function saveProjectMeta(metaPath, data) {
  data.updated = new Date().toISOString().split('T')[0];
  fs.writeFileSync(metaPath, JSON.stringify(data, null, 2) + '\n');
}

module.exports = { detectProjectType, loadProjectMeta, saveProjectMeta };
