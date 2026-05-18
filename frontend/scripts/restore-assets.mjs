import { spawnSync } from 'node:child_process'
import { createReadStream, createWriteStream, existsSync, mkdirSync, readdirSync, rmSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = dirname(dirname(fileURLToPath(import.meta.url)))
const partsDir = join(root, 'asset-packages', 'parts')
const publicDir = join(root, 'public')
const tmpZip = join(root, 'asset-packages', 'public-assets.zip')

if (!existsSync(partsDir)) {
  throw new Error(`Missing asset parts directory: ${partsDir}`)
}

mkdirSync(publicDir, { recursive: true })
mkdirSync(dirname(tmpZip), { recursive: true })

const parts = readdirSync(partsDir)
  .filter(name => name.startsWith('public-assets.zip.'))
  .sort()

if (!parts.length) {
  throw new Error(`No asset parts found in: ${partsDir}`)
}

await mergeParts(parts)
extractZip()
rmSync(tmpZip, { force: true })

async function mergeParts(parts) {
  const output = createWriteStream(tmpZip)

  for (const part of parts) {
    await new Promise((resolve, reject) => {
      const input = createReadStream(join(partsDir, part))
      input.on('error', reject)
      input.on('end', resolve)
      input.pipe(output, { end: false })
    })
  }

  await new Promise((resolve, reject) => {
    output.end(resolve)
    output.on('error', reject)
  })
}

function extractZip() {
  const commands = process.platform === 'win32'
    ? [
        ['powershell', ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', `Expand-Archive -LiteralPath '${tmpZip}' -DestinationPath '${publicDir}' -Force`]],
        ['python', ['-m', 'zipfile', '-e', tmpZip, publicDir]],
      ]
    : [
        ['unzip', ['-oq', tmpZip, '-d', publicDir]],
        ['python3', ['-m', 'zipfile', '-e', tmpZip, publicDir]],
        ['python', ['-m', 'zipfile', '-e', tmpZip, publicDir]],
      ]

  for (const [command, args] of commands) {
    const result = spawnSync(command, args, { stdio: 'inherit' })
    if (result.status === 0)
      return
  }

  throw new Error('Could not extract assets. Install unzip or python in the deployment image.')
}
