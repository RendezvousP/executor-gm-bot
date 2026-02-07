const fs = require('fs');
const path = require('path');
const https = require('https');

const REGISTRY_PATH = path.join(__dirname, 'skill_registry.json');
const LOG_PATH = path.join(__dirname, 'update_log.txt');
const CONCURRENCY_LIMIT = 5; // Batch size

function log(message) {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] ${message}`;
    console.log(logMessage);
    fs.appendFileSync(LOG_PATH, logMessage + '\n');
}

function fetchUrl(url) {
    return new Promise((resolve, reject) => {
        https.get(url, (res) => {
            // Handle Redirects
            if (res.statusCode === 301 || res.statusCode === 302) {
                if (res.headers.location) {
                    fetchUrl(res.headers.location).then(resolve).catch(reject);
                    return;
                }
            }
            if (res.statusCode !== 200) {
                res.resume();
                reject(new Error(`Status Code: ${res.statusCode}`));
                return;
            }
            let data = '';
            res.on('data', (chunk) => data += chunk);
            res.on('end', () => resolve(data));
        }).on('error', reject);
    });
}

async function processSkill(skill) {
    const skillPath = path.join(__dirname, skill.name, 'SKILL.md');
    log(`[Checking] ${skill.name}...`);

    try {
        // [MODIFIED] Handle Local Sources for Titan Class Skills
        if (skill.source.startsWith('./') || skill.source.startsWith('.\\')) {
            const localSourcePath = path.join(__dirname, '..', skill.source); // Resolve relative to repo root

            if (fs.existsSync(skillPath)) {
                log(`  [OK] ${skill.name} verified (Local Titan Skill).`);
                return { success: true };
            } else {
                throw new Error(`Local skill file missing at ${skillPath}`);
            }
        }

        // Handle Remote Sources (Legacy/Updates)
        const content = await fetchUrl(skill.source);

        if (!content.trim().startsWith('---')) {
            throw new Error('Invalid content format (missing frontmatter)');
        }

        const skillDir = path.dirname(skillPath);
        if (!fs.existsSync(skillDir)) {
            fs.mkdirSync(skillDir, { recursive: true });
        }

        fs.writeFileSync(skillPath, content);
        log(`  [OK] ${skill.name} updated.`);
        return { success: true };

    } catch (error) {
        log(`  [FAIL] ${skill.name}: ${error.message}`);
        if (skill.synthesized && fs.existsSync(skillPath)) {
            log(`  -> Preserved local version.`);
        }
        return { success: false };
    }
}

async function updateSkills() {
    log('=== Starting Titan Update Engine (Parallel) ===');

    if (!fs.existsSync(REGISTRY_PATH)) {
        log('ERROR: Registry file not found!');
        return;
    }

    const registry = JSON.parse(fs.readFileSync(REGISTRY_PATH, 'utf8'));
    const skills = registry.skills;
    let completed = 0;
    let successCount = 0;
    let failCount = 0;

    // Parallel Execution Queue
    for (let i = 0; i < skills.length; i += CONCURRENCY_LIMIT) {
        const batch = skills.slice(i, i + CONCURRENCY_LIMIT);
        const results = await Promise.all(batch.map(processSkill));

        results.forEach(r => r.success ? successCount++ : failCount++);
        completed += batch.length;
        console.log(`Progress: ${Math.min(completed, skills.length)}/${skills.length}`);
    }

    log('========================================');
    log(`Update Complete.`);
    log(`Success: ${successCount}`);
    log(`Failed (Preserved): ${failCount}`);
    log('========================================');
}

updateSkills();
