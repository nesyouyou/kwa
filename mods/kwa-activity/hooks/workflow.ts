// Le modèle du panneau : quel workflow, quelle étape, et le dessin SVG. Fonctions pures, testées sans moteur.
import type { Brick, Step, Usage } from '../types'

export type Kind = 'skill' | 'garde' | 'hook' | 'agent' | 'vous' | 'doc'
// aborted : interrompue par l'utilisateur ; passed : ni vue ni faite, mais une étape plus loin a été atteinte
export type Status = 'done' | 'run' | 'passed' | 'next' | 'denied' | 'aborted'
// count / live : pour la boîte des sous-agents d'une brique, combien ont été lancés et combien tournent encore
export type Row = { brick: Brick; kind: Kind; name: string; status: Status; ms: number | null; extra: boolean; count?: number; live?: number; aborted?: number }
export type Agent = { name: string; task: string; ms: number }
// running : les sous-agents qui tournent ; done : ceux qui ont fini ; peak : le plus grand nombre en même temps
export type Swarm = { running: Agent[]; done: number; peak: number }
// detected : une skill Kwa a désigné le workflow ; sinon `key` n'est que le parcours montré par défaut
// touched : briques où les outils ont travaillé ; current : la brique de la dernière activité des outils
export type Model = { key: string; title: string; why: string; detected: boolean; rows: Row[]; swarm: Swarm; touched: Brick[]; current: Brick | null }
export type Activity = { touched: Brick[]; current: Brick | null }

export const BRICKS: [Brick, string][] = [
  ['cadrer', 'Cadrer'], ['faire', 'Faire'], ['prouver', 'Prouver'],
  ['relire', 'Relire'], ['livrer', 'Livrer'], ['capitaliser', 'Capitaliser'],
]

// Les cinq workflows du site de Kwa (docs/site/src/flows.py), étape par étape.
const FLOWS: Record<string, { title: string; steps: [Brick, Kind, string][] }> = {
  feature: { title: 'Développer une fonctionnalité', steps: [
    ['cadrer', 'skill', '/kwa:brainstorm'], ['cadrer', 'vous', 'validation'], ['cadrer', 'skill', '/kwa:plan'],
    ['faire', 'garde', 'guard-write'], ['faire', 'skill', '/kwa:start-dev'], ['faire', 'skill', '/kwa:agents'],
    ['prouver', 'skill', '/kwa:tdd'], ['prouver', 'skill', '/kwa:verify'],
    ['relire', 'agent', 'kwa:reviewer'], ['relire', 'skill', '/kwa:review-feedback'],
    ['livrer', 'vous', 'push'], ['livrer', 'skill', '/kwa:ship'], ['livrer', 'vous', 'fusion'],
    ['capitaliser', 'skill', '/kwa:learn'], ['capitaliser', 'doc', '/kwa:handoff']] },
  bug: { title: 'Corriger un bug', steps: [
    ['cadrer', 'skill', '/kwa:debug'], ['cadrer', 'vous', 'cause'], ['faire', 'skill', '/kwa:start-dev'],
    ['prouver', 'skill', '/kwa:tdd'], ['prouver', 'skill', '/kwa:simple'], ['prouver', 'hook', 'verify-stop'], ['prouver', 'skill', '/kwa:verify'],
    ['livrer', 'skill', '/kwa:commit'], ['livrer', 'garde', 'guard-github'], ['livrer', 'skill', '/kwa:ship'],
    ['capitaliser', 'skill', '/kwa:learn']] },
  review: { title: 'Relire', steps: [
    ['relire', 'skill', '/kwa:review'], ['relire', 'agent', 'kwa:reviewer'], ['relire', 'hook', 'readonly-bash'],
    ['relire', 'skill', '/kwa:review-feedback'], ['faire', 'skill', '/kwa:tdd'], ['prouver', 'skill', '/kwa:verify'],
    ['livrer', 'vous', 'décision']] },
  ship: { title: 'Livrer', steps: [
    ['prouver', 'skill', '/kwa:verify'], ['livrer', 'skill', '/kwa:commit'], ['livrer', 'garde', 'guard-git'],
    ['livrer', 'vous', 'push'], ['livrer', 'garde', 'guard-github'], ['livrer', 'vous', 'fusion'],
    ['livrer', 'skill', '/kwa:deploy'], ['capitaliser', 'skill', '/kwa:learn']] },
  learn: { title: 'Capitaliser', steps: [
    ['cadrer', 'hook', 'memory-context'], ['faire', 'hook', 'signal-prompt'], ['faire', 'garde', 'guard-write'],
    ['capitaliser', 'hook', 'memory-nudge'], ['capitaliser', 'skill', '/kwa:learn'], ['capitaliser', 'vous', 'accord'],
    ['capitaliser', 'doc', '/kwa:handoff']] },
}
// La première skill de la session dit de quel workflow il s'agit.
const FLOW_OF: Record<string, string> = {
  '/kwa:debug': 'bug', '/kwa:review': 'review', '/kwa:review-feedback': 'review',
  '/kwa:commit': 'ship', '/kwa:ship': 'ship', '/kwa:deploy': 'ship', '/kwa:learn': 'learn', '/kwa:handoff': 'learn',
}

// Sans skill, le préfixe de la branche dit le workflow (même table que `kwa activity`).
const BRANCH_FLOW: Record<string, string> = { fix: 'bug', hotfix: 'bug', feat: 'feature', feature: 'feature' }
export const flowOfBranch = (branch: string | null | undefined): string | null =>
  (branch?.includes('/') && BRANCH_FLOW[branch.split('/')[0]!]) || null

// Les mêmes briques que les workflows animés du site de Kwa (docs/site/src/flows.py)
export const BRICK_OF: Record<string, Brick> = {
  brainstorm: 'cadrer', interview: 'cadrer', plan: 'cadrer', debug: 'cadrer', prototype: 'cadrer', questionnaire: 'cadrer',
  tickets: 'cadrer', research: 'cadrer', domain: 'cadrer', architecture: 'cadrer', rephrase: 'cadrer',
  init: 'faire', 'start-dev': 'faire', agents: 'faire', execute: 'faire', parallel: 'faire', simple: 'faire', conflicts: 'faire',
  tdd: 'prouver', verify: 'prouver', audit: 'prouver',
  review: 'relire', 'review-feedback': 'relire',
  commit: 'livrer', ship: 'livrer', deploy: 'livrer', testflight: 'livrer', humanize: 'livrer',
  learn: 'capitaliser', handoff: 'capitaliser', 'agent-docs': 'capitaliser', teach: 'capitaliser',
}

// Un refus d'un garde de Kwa (« Kwa — … ») : quel garde, et la brique où il tombe.
export const guardOf = (text: string) =>
  /code sur main/.test(text) ? 'guard-write' : /PR|Closes|preuve/.test(text) ? 'guard-github' : /push|commit/.test(text) ? 'guard-git' : 'garde'
export const guardBrick = (name: string, last?: Brick): Brick => (name === 'guard-write' ? 'faire' : name === 'garde' ? last ?? 'faire' : 'livrer')

export type Restored = { steps: Step[]; first: string | null; touched: Brick[]; branch: string | null }

// Le journal d'activité de Kwa (module memory : une ligne JSON par événement, écrite par ses hooks) relu en étapes
// du Mod. Il sert quand l'état de session du Mod est vide alors que la session a déjà travaillé : session reprise,
// Mod installé en cours de route. Ce qui n'a pas de fin dans le journal est clos à son dernier événement : rien
// n'indique que cela tourne encore, et les étapes vues en direct prennent le relais.
export function fromJournal(text: string): Restored {
  const events: Record<string, unknown>[] = []
  for (const line of text.split('\n')) {
    if (!line.trim()) continue
    try {
      events.push(JSON.parse(line))
    } catch {
      // une ligne coupée (écriture en cours) est ignorée
    }
  }
  const at = (e: Record<string, unknown>) => Math.round(Number(e.ts ?? 0) * 1000)
  const steps: Step[] = []
  const touched: Brick[] = []
  let first: string | null = null
  let branch: string | null = null
  const lastSkill = () => [...steps].reverse().find(s => s.kind === 'skill')
  const closeSkills = (t: number) => steps.forEach((s, k) => { if (s.kind === 'skill' && s.endedAt === null) steps[k] = { ...s, endedAt: t } })
  events.forEach((e, i) => {
    const t = at(e)
    const name = String(e.name ?? '')
    const base = { id: `j${i}-${t}`, task: '', startedAt: t, endedAt: null, isAborted: false }
    if (e.kind === 'session') branch ??= (e.branch as string) || null
    else if (e.kind === 'turn') closeSkills(t)
    else if (e.kind === 'skill') {
      const skill = name.replace(/^\//, '')
      const brick = skill.startsWith('kwa:') ? BRICK_OF[skill.slice(4)] : undefined
      if (!brick) return
      closeSkills(t)
      first ??= `/${skill}`
      steps.push({ ...base, kind: 'skill', name: `/${skill}`, brick })
    } else if (e.kind === 'agent') {
      const n = name || 'agent'
      steps.push({ ...base, kind: 'agent', name: n, task: String(e.target ?? ''), brick: /review/.test(n) ? 'relire' : lastSkill()?.brick ?? 'faire' })
    } else if (e.kind === 'agent-end') {
      const k = steps.findIndex(s => s.kind === 'agent' && s.endedAt === null && s.name === (name || 'agent'))
      if (k >= 0) steps[k] = { ...steps[k]!, endedAt: t }
    } else if (e.kind === 'deny') {
      const g = guardOf(String(e.reason ?? ''))
      steps.push({ ...base, kind: 'garde', name: g, brick: guardBrick(g, lastSkill()?.brick), endedAt: t })
    } else if (e.kind === 'tool' && BRICKS.some(([b]) => b === e.brick)) {
      const b = e.brick as Brick
      if (touched[touched.length - 1] !== b) touched.splice(0, touched.length, ...touched.filter(x => x !== b), b)
    }
  })
  const end = events.length ? at(events[events.length - 1]!) : 0
  return { steps: steps.map(s => (s.endedAt === null ? { ...s, endedAt: end } : s)), first, touched, branch }
}

const matches = (row: [Brick, Kind, string], s: Step) =>
  // les sous-agents ne sont pas appariés ici : ils sont comptés à part, par brique
  (s.kind === 'skill' && row[2] === s.name) || (s.kind === 'garde' && row[1] === 'garde' && row[2] === s.name)

const ORDER = (b: Brick) => BRICKS.findIndex(([x]) => x === b)
// une ligne hors parcours va après la dernière ligne d'une brique qui ne vient pas après la sienne
const insertAt = (rows: Row[], b: Brick) => {
  let at = 0
  rows.forEach((r, i) => { if (ORDER(r.brick) <= ORDER(b)) at = i + 1 })
  return at
}
const stepStatus = (s: Step): Status => (s.kind === 'garde' ? 'denied' : s.endedAt === null ? 'run' : s.isAborted ? 'aborted' : 'done')

// `first` : la première skill Kwa de la session, gardée à part pour que le workflow détecté ne change pas quand
// la liste des étapes est tronquée. `branch` : la branche de la session, qui dit le workflow tant qu'aucune skill ne l'a fait.
export function model(steps: Step[], now: number, first: string | null = steps.find(s => s.kind === 'skill')?.name ?? null,
  activity: Activity = { touched: [], current: null }, branch: string | null = null): Model {
  const byBranch = first ? null : flowOfBranch(branch)
  const key = (first && FLOW_OF[first]) || byBranch || 'feature'
  const flow = FLOWS[key]!
  const why = first ? `d'après ${first}` : byBranch ? `d'après la branche ${branch}` : 'en attente d’une skill'
  const used = new Set<Step>()
  const rows: Row[] = flow.steps.map(def => {
    const hit = [...steps].reverse().find(s => !used.has(s) && matches(def, s))
    if (!hit) return { brick: def[0], kind: def[1], name: def[2], status: 'next', ms: null, extra: false }
    used.add(hit)
    return { brick: def[0], kind: def[1], name: def[2], status: stepStatus(hit), ms: (hit.endedAt ?? now) - hit.startedAt, extra: false }
  })
  // les sous-agents d'une brique tournent souvent en parallèle : une seule boîte par brique, qui les compte
  for (const s of steps) {
    if (s.kind !== 'agent') continue
    let row = rows.find(r => r.brick === s.brick && r.kind === 'agent')
    if (!row) {
      row = { brick: s.brick, kind: 'agent', name: s.name, status: 'next', ms: null, extra: true }
      rows.splice(insertAt(rows, s.brick), 0, row)
    }
    if (!row.count) row.name = s.name
    else if (row.name !== s.name) row.name = 'sous-agents'
    row.count = (row.count ?? 0) + 1
    row.live = (row.live ?? 0) + (s.endedAt === null ? 1 : 0)
    if (s.endedAt !== null && s.isAborted) row.aborted = (row.aborted ?? 0) + 1
    // la boîte n'est « interrompue » que si tous ses agents le sont ; sinon elle est faite et compte les interrompus
    row.status = row.live ? 'run' : row.aborted === row.count ? 'aborted' : 'done'
    row.ms = Math.max(row.ms ?? 0, (s.endedAt ?? now) - s.startedAt)
    used.add(s)
  }
  // une skill ou un refus hors du parcours type s'ajoute dans sa brique, à sa place dans l'ordre des briques
  // une même étape répétée (un garde qui refuse dix fois, une skill relancée) se compte dans une seule boîte
  for (const s of steps) {
    if (used.has(s)) continue
    const kind: Kind = s.kind === 'garde' ? 'garde' : 'skill'
    const same = rows.find(r => r.brick === s.brick && r.kind === kind && r.name === s.name && r.status !== 'next')
    if (same) {
      same.count = (same.count ?? 1) + 1
      // une ligne du parcours porte déjà l'étape la plus récente ; une ligne ajoutée prend la plus récente vue
      if (same.extra) {
        same.status = stepStatus(s)
        same.ms = (s.endedAt ?? now) - s.startedAt
      }
      continue
    }
    const row: Row = { brick: s.brick, kind, name: s.name, status: stepStatus(s), ms: (s.endedAt ?? now) - s.startedAt, extra: true }
    rows.splice(insertAt(rows, s.brick), 0, row)
  }
  // une étape du parcours type qui précède la dernière étape type atteinte est passée, même sans trace (une
  // validation, un hook) ; les lignes ajoutées ne font rien passer
  let last = -1
  rows.forEach((r, i) => { if (!r.extra && r.status !== 'next') last = i })
  rows.forEach((r, i) => { if (r.status === 'next' && !r.extra && i < last) r.status = 'passed' })
  return { key, title: flow.title, why, detected: first !== null || byBranch !== null, rows, swarm: swarm(steps, now), ...activity }
}

// Ce que fait un appel d'outil, en une brique et quelques mots. `verify` : les commandes de vérification de la
// politique du projet. Une commande du shell qui ne relève d'aucune brique garde son libellé, sans brique.
const TEST = /\b(test|tests|pytest|unittest|jest|vitest|mocha|tsc|lint|eslint|typecheck|go test|cargo (test|check)|mvn (test|verify)|gradle (test|check)|dotnet (build|test))\b/
const SHIP = /\b(git (commit|push|merge|tag)|gh pr (create|merge))\b/
const base = (p: unknown) => String(p ?? '').split('/').filter(Boolean).pop() ?? ''
export function classify(tool: string, args: Record<string, unknown>, verify: string[] = []): { brick: Brick | null; label: string } | null {
  if (tool === 'Read' || tool === 'NotebookRead') return { brick: 'cadrer', label: `lit ${base(args.file_path ?? args.notebook_path)}` }
  if (tool === 'Grep') return { brick: 'cadrer', label: `cherche « ${cut(String(args.pattern ?? ''), 24)} »` }
  if (tool === 'Glob') return { brick: 'cadrer', label: `cherche des fichiers ${cut(String(args.pattern ?? ''), 24)}` }
  if (tool === 'WebFetch' || tool === 'WebSearch') return { brick: 'cadrer', label: 'consulte le web' }
  if (tool === 'Write') return { brick: 'faire', label: `écrit ${base(args.file_path)}` }
  if (tool === 'Edit' || tool === 'MultiEdit' || tool === 'NotebookEdit') return { brick: 'faire', label: `modifie ${base(args.file_path ?? args.notebook_path)}` }
  if (tool !== 'Bash') return null
  const cmd = String(args.command ?? '').trim()
  if (!cmd) return null
  const shown = cut(cmd.split('\n')[0]!, 48)
  if (verify.some(v => v && cmd.includes(v)) || TEST.test(cmd)) return { brick: 'prouver', label: `lance ${shown}` }
  if (SHIP.test(cmd)) return { brick: 'livrer', label: shown }
  return { brick: null, label: `exécute ${shown}` }
}

function swarm(steps: Step[], now: number): Swarm {
  const agents = steps.filter(s => s.kind === 'agent')
  const edges = agents.flatMap(a => [[a.startedAt, 1], [a.endedAt ?? Infinity, -1]] as [number, number][])
    .sort((a, b) => a[0] - b[0] || a[1] - b[1])
  let live = 0, peak = 0
  for (const [, d] of edges) peak = Math.max(peak, (live += d))
  const running = agents.filter(a => a.endedAt === null).map(a => ({ name: a.name, task: a.task, ms: now - a.startedAt }))
  return { running, done: agents.length - running.length, peak }
}

// Les cinq workflows, dans l'ordre des ronds du haut : celui détecté s'allume.
export const WORKFLOWS: [string, string, string][] = [
  ['feature', 'Feature', '#0ea5e9'], ['bug', 'Bug', '#ef4444'], ['review', 'Relire', '#a855f7'],
  ['ship', 'Livrer', '#f97316'], ['learn', 'Capitaliser', '#eab308'],
]

const BRICK_COLOR: Record<Brick, string> = {
  cadrer: '#6366f1', faire: '#0ea5e9', prouver: '#10b981', relire: '#a855f7', livrer: '#f97316', capitaliser: '#eab308',
}
const KIND_COLOR: Record<Kind, string> = {
  skill: '#3b82f6', garde: '#ef4444', hook: '#f59e0b', agent: '#8b5cf6', vous: '#22c55e', doc: '#14b8a6',
}
const KIND_LABEL: Record<Kind, string> = { skill: 'skill', garde: 'garde', hook: 'hook', agent: 'sous-agent', vous: 'vous', doc: 'relais' }

// les caractères de contrôle sont interdits en XML et casseraient tout le dessin
const esc = (t: string) => t.replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/g, '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
export const duration = (ms: number) => (ms < 60000 ? `${Math.max(0, Math.round(ms / 1000))} s` : `${Math.round(ms / 60000)} min`)
export const kilo = (n: number) => (n >= 1000 ? `${Math.round(n / 1000)} k` : `${n}`)
export const money = (usd: number) => `${usd.toFixed(2).replace('.', ',')} $`

// Un agent en cours est-il fini ? `status` est son état dans $.agent.list(), absent s'il n'y figure pas. Un agent de
// workflow n'y figure jamais : seule sa fin de tour le clôt, sauf `staleMs` après son lancement (lancé à distance, il
// n'en aura pas ; un agent de workflow légitime plus long que ce délai sera clos lui aussi).
const OVER = new Set(['completed', 'failed', 'killed', 'idle'])
export function isOver(s: Step, status: string | undefined, now: number, staleMs = 2 * 60 * 60 * 1000): boolean {
  if (status !== undefined) return OVER.has(status)
  return !s.viaWorkflow || now - s.startedAt >= staleMs
}

// La brique ouverte : celle de l'étape en cours, sinon celle de la dernière étape atteinte. Une seule à la fois,
// comme sur la page d'accueil du site de Kwa.
export function openBrick(m: Model): Brick | null {
  const run = m.rows.find(r => r.status === 'run')
  if (run) return run.brick
  if (m.current) return m.current   // sans skill en cours, la brique de la dernière activité des outils
  const reached = m.rows.filter(r => r.status !== 'next' && r.status !== 'passed')
  return reached.length ? reached[reached.length - 1]!.brick : null
}

// Le dessin : un logigramme vertical. Chaque brique est un cadre ; fermée, elle montre une pastille par étape ;
// ouverte, une boîte par étape, reliées par des flèches qui descendent.
// `unfoldAgo` : depuis combien de millisecondes on est entré dans la brique ouverte. Tant que le dépliage n'est
// pas fini (le cadre grandit, ce qui suit glisse, les étapes arrivent en cascade), il est dessiné reparti de là où
// il en est, pour qu'un nouveau rendu en plein milieu ne le coupe pas. `intro` remplit l'anneau du contexte.
export type Drawing = { source: string; width: number; height: number }
// live : les chronomètres des étapes en cours ; card : la carte du coût et du contexte. Le Mod les retire tous deux
// du schéma et les affiche en éléments natifs, pour que le SVG ne change qu'avec les étapes : un nouveau SVG recharge
// le cadre qui le montre, et c'est ce rechargement qui clignote.
export type DrawOptions = { unfoldAgo?: number | null; intro?: boolean; live?: boolean; card?: boolean | 'context' }
const WIDTH = 360
const UNFOLD_MS = 1500
const EASE = 'calcMode="spline" keyTimes="0;1" keySplines=".65 0 .25 1"'
// le moulinet d'un sous-agent : un anneau pâle et un arc qui tourne
const spinner = (x: number, y: number, r: number, color: string, w = 2.5, dur = 0.9) =>
  `<circle cx="${x}" cy="${y}" r="${r}" fill="none" stroke="${color}" stroke-opacity=".2" stroke-width="${w}"/>` +
  `<path d="M${x} ${y - r} A${r} ${r} 0 0 1 ${x + r} ${y}" fill="none" stroke="${color}" stroke-width="${w}" stroke-linecap="round">` +
  `<animateTransform attributeName="transform" type="rotate" from="0 ${x} ${y}" to="360 ${x} ${y}" dur="${dur}s" repeatCount="indefinite"/></path>`
const contextPercent = (u: Usage | null) => u?.percent ?? (u?.tokens != null && u.window ? (100 * u.tokens) / u.window : null)
// L'anneau du remplissage du contexte : vert sous 50 %, orange jusqu'à 80 %, rouge au-delà.
function ringMarkup(pct: number | null, intro: boolean, cx: number, cy: number): string {
  const tint = pct == null ? '#94a3b8' : pct < 50 ? '#10b981' : pct < 80 ? '#f59e0b' : '#ef4444'
  const R = 32, C = 2 * Math.PI * R
  const dash = pct == null ? 0 : (C * Math.min(pct, 100)) / 100
  return `<g transform="translate(${cx} ${cy}) rotate(-90)"><circle r="${R}" class="track"/>` +
    `<circle r="${R}" fill="none" stroke="${tint}" stroke-width="10" stroke-linecap="round" stroke-dasharray="${dash} ${C}">` +
    (intro ? `<animate attributeName="stroke-dasharray" from="0 ${C}" to="${dash} ${C}" dur="1s"/>` : '') + `</circle></g>` +
    `<text x="${cx}" y="${cy + 5}" class="pct" text-anchor="middle">${pct == null ? '—' : Math.round(pct) + ' %'}</text>`
}
const cut = (t: string, n: number) => { const c = [...t]; return c.length > n ? c.slice(0, n - 1).join('') + '…' : t }
export function svg(m: Model, u: Usage | null, sessionMs: number, { unfoldAgo = null, intro = false, live = true, card = true }: DrawOptions = {}): Drawing {
  const since = (ms: number | null) => (live ? ` · ${duration(ms ?? 0)}` : '')
  const animate = unfoldAgo !== null && unfoldAgo < UNFOLD_MS
  const begin = animate ? ` begin="${(-unfoldAgo / 1000).toFixed(2)}s"` : ''
  const W = WIDTH, CX = W / 2, BOX = 38, GAP = 18, HEAD = 44, MORPH = 0.65
  const open = openBrick(m)
  const reachedRow = (r: Row) => r.status !== 'next'
  const arrow = (x: number, y1: number, y2: number, state: 'on' | 'run' | 'off', color: string) => {
    const tint = state === 'run' ? ` style="stroke:${color}"` : ''
    return `<line x1="${x}" y1="${y1}" x2="${x}" y2="${y2 - 1}" class="ar ${state}"${tint}>` +
      (state === 'run' ? `<animate attributeName="stroke-dashoffset" values="12;0" dur=".6s" repeatCount="indefinite"/>` : '') + `</line>` +
      `<path d="M${x - 5} ${y2 - 7} L${x} ${y2} L${x + 5} ${y2 - 7}" class="tip ${state}"${tint}/>`
  }
  // apparition retardée d'une étape : invisible jusqu'à `delay`, puis fondu et petite montée
  const cascade = (delay: number) => {
    const dur = delay + 0.5, k = (delay / dur).toFixed(3)
    return `<animate attributeName="opacity" values="0;0;1" keyTimes="0;${k};1" dur="${dur}s"${begin} fill="freeze"/>` +
      `<animateTransform attributeName="transform" type="translate" values="0 8;0 8;0 0" keyTimes="0;${k};1" dur="${dur}s"${begin} fill="freeze"/>`
  }

  let before = ''   // ce qui est au-dessus de la brique ouverte et ne bouge pas
  let after = ''    // ce qui est en dessous et glisse pendant le dépliage
  let grow = 0
  // les cinq ronds des workflows, celui détecté allumé
  const col = (W - 20) / WORKFLOWS.length
  const dots = WORKFLOWS.map(([flow, label, c], i) => {
    const on = m.detected && flow === m.key
    const x = 10 + col * i + col / 2, cy = 82
    return `<g class="wf${on ? ' on' : ''}" data-flow="${flow}">` + (on
      ? `<circle cx="${x}" cy="${cy}" r="17" fill="none" stroke="${c}" stroke-width="2"><animate attributeName="opacity" values=".7;.1;.7" dur="2s" repeatCount="indefinite"/></circle>` +
        `<circle cx="${x}" cy="${cy}" r="13" fill="${c}"/><circle cx="${x}" cy="${cy}" r="4.5" fill="#fff"/>`
      : `<circle cx="${x}" cy="${cy}" r="11" class="hollow" style="stroke:${c}" stroke-opacity=".45"/>`) +
      `<text x="${x}" y="${cy + 30}" text-anchor="middle" class="wl${on ? ' on' : ''}"${on ? ` style="fill:${c}"` : ''}>${label}</text></g>`
  }).join('')
  const head = `<text x="16" y="30" class="title">${esc(m.title)}</text><text x="16" y="50" class="meta">workflow détecté ${esc(m.why)}</text>${dots}`
  let y = 132
  let prevBottom = 0
  let prevReached = false
  let n = 0
  for (const [b, label] of BRICKS) {
    const rows = m.rows.filter(r => r.brick === b)
    if (!rows.length) continue
    n++
    const color = BRICK_COLOR[b]
    const isOpen = b === open
    const live = rows.some(r => r.status === 'run')
    const reached = rows.some(reachedRow) || m.touched.includes(b)
    const isDone = !isOpen && rows.some(r => r.status === 'done') && rows.every(r => r.status === 'done' || r.status === 'passed')
    const denied = rows.reduce((n, r) => n + (r.status === 'denied' ? r.count ?? 1 : 0), 0)
    let out = ''
    if (prevBottom) out += arrow(CX, prevBottom, y, reached ? (live && !prevReached ? 'run' : 'on') : 'off', color)
    const h = isOpen ? HEAD + rows.length * BOX + (rows.length - 1) * GAP + 14 : HEAD
    const grows = isOpen && animate
    const hAnim = grows ? `<animate attributeName="height" from="${HEAD}" to="${h}" dur="${MORPH}s"${begin} ${EASE} fill="freeze"/>` : ''
    const frameOpacity = reached ? (isOpen ? 0.8 : 0.45) : 0.25
    out += `<g${isDone ? ' opacity=".8"' : ''}>` +
      `<rect x="10" y="${y}" width="${W - 20}" height="${h}" rx="16" class="frame${isOpen ? ' open' : ''}" style="stroke:${color}" stroke-opacity="${frameOpacity}"${reached ? '' : ' stroke-dasharray="5 5"'}>${hAnim}</rect>` +
      `<rect x="10" y="${y}" width="${W - 20}" height="${h}" rx="16" fill="${color}" fill-opacity="${isOpen ? 0.09 : reached ? 0.05 : 0.02}">${hAnim}</rect>`
    // l'en-tête : numéro (coche quand la brique est finie), nom, puis pastilles des étapes si elle est fermée
    const nx = 32, ny = y + HEAD / 2
    out += isDone
      ? `<circle cx="${nx}" cy="${ny}" r="11" fill="#10b981"/><path d="M${nx - 4.5} ${ny} l3 3 l6 -6.5" class="tick"/>`
      : isOpen
        ? `<circle cx="${nx}" cy="${ny}" r="11" fill="${color}">${live ? `<animate attributeName="opacity" values="1;.55;1" dur="1.4s" repeatCount="indefinite"/>` : ''}</circle><text x="${nx}" y="${ny + 4}" class="num on" text-anchor="middle">${n}</text>`
        : `<circle cx="${nx}" cy="${ny}" r="11" class="hollow" style="stroke:${color}" stroke-opacity="${reached ? 0.8 : 0.4}"/><text x="${nx}" y="${ny + 4}" class="num t-${b}" text-anchor="middle" opacity="${reached ? 1 : 0.6}">${n}</text>`
    out += `<text x="52" y="${ny + 5}" class="bh t-${b}" opacity="${reached ? 1 : 0.55}">${label}</text>`
    if (!isOpen) {
      // une pastille par étape, à droite : verte faite, rouge refusée, pâle passée, vide à venir
      rows.forEach((r, i) => {
        const px = W - 26 - (rows.length - 1 - i) * 14
        const fill = r.status === 'done' ? '#10b981' : r.status === 'denied' ? '#ef4444' : r.status === 'aborted' ? '#71717a' : r.status === 'run' ? color : null
        out += fill ? `<circle cx="${px}" cy="${ny}" r="4.5" fill="${fill}"/>`
          : r.status === 'passed' ? `<circle cx="${px}" cy="${ny}" r="4.5" fill="${KIND_COLOR[r.kind]}" opacity=".35"/>`
          : `<circle cx="${px}" cy="${ny}" r="4" class="hollow" style="stroke:${KIND_COLOR[r.kind]}" stroke-opacity=".5"/>`
      })
    } else {
      out += `<text x="${W - 24}" y="${ny + 4}" class="meta" text-anchor="end">${rows.filter(r => r.status === 'done' || r.status === 'passed').length}/${rows.length}${denied ? ` · ${denied} refus` : ''}</text>`
      let by = y + HEAD
      rows.forEach((r, i) => {
        let row = ''
        if (i > 0) row += arrow(CX, by - GAP, by, r.status === 'run' ? 'run' : reachedRow(r) && reachedRow(rows[i - 1]!) ? 'on' : 'off', color)
        const c = KIND_COLOR[r.kind]
        const bx = 24, bw = W - 48, cy = by + BOX / 2
        const ring = r.status === 'denied' ? '#ef4444' : r.status === 'run' ? color : r.status === 'next' ? undefined : c
        row += `<rect x="${bx}" y="${by}" width="${bw}" height="${BOX}" rx="10" class="box${r.status === 'next' ? ' off' : ''}"` +
          `${ring ? ` style="stroke:${ring}"` : ''}${r.status === 'run' ? ' stroke-width="2.5"' : ''}>` +
          (r.status === 'run' ? `<animate attributeName="stroke-opacity" values="1;.35;1" dur="1.4s" repeatCount="indefinite"/>` : '') + `</rect>`
        if (r.status === 'run') row += `<rect x="${bx}" y="${by}" width="${bw}" height="${BOX}" rx="10" fill="${color}" fill-opacity=".14"/>`
        if (r.status === 'denied') row += `<rect x="${bx}" y="${by}" width="${bw}" height="${BOX}" rx="10" fill="#ef4444" fill-opacity=".1"/>`
        const ix = bx + 20
        if (r.status === 'done') row += `<circle cx="${ix}" cy="${cy}" r="9" fill="#10b981"/><path d="M${ix - 4} ${cy} l3 3 l5 -6" class="tick"/>`
        else if (r.status === 'run' && r.kind === 'agent') row += spinner(ix, cy, 8, color)
        else if (r.status === 'run') row += `<circle cx="${ix}" cy="${cy}" r="8" fill="${color}"/>` +
          `<circle cx="${ix}" cy="${cy}" r="8" fill="none" stroke="${color}" stroke-width="2"><animate attributeName="r" values="8;15" dur="1.4s" repeatCount="indefinite"/><animate attributeName="opacity" values=".8;0" dur="1.4s" repeatCount="indefinite"/></circle>`
        else if (r.status === 'denied') row += `<circle cx="${ix}" cy="${cy}" r="9" fill="#ef4444"/><path d="M${ix - 3.5} ${cy - 3.5} l7 7 M${ix + 3.5} ${cy - 3.5} l-7 7" class="tick"/>`
        else if (r.status === 'aborted') row += `<circle cx="${ix}" cy="${cy}" r="9" fill="#71717a"/><path d="M${ix - 3.5} ${cy - 3.5} l7 7 M${ix + 3.5} ${cy - 3.5} l-7 7" class="tick"/>`
        else if (r.status === 'passed') row += `<circle cx="${ix}" cy="${cy}" r="5" fill="${c}" opacity=".5"/>`
        else row += `<circle cx="${ix}" cy="${cy}" r="7" class="hollow" style="stroke:${c}" stroke-opacity=".5"/>`
        const cls = r.status === 'next' ? 'sn dim' : r.status === 'run' ? 'sn now' : r.status === 'passed' ? 'sn soft' : 'sn'
        const meta = r.status === 'denied' ? 'refusé' : r.status === 'aborted' ? 'interrompue' : r.status === 'run' ? `en cours${since(r.ms)}` : r.ms !== null ? duration(r.ms) : r.status === 'passed' ? 'passée' : KIND_LABEL[r.kind]
        const label = r.count && r.count > 1 ? `${r.name} ×${r.count}` : r.name
        const metaRow = r.kind === 'agent' && r.live && r.count && r.count > 1 ? `${r.live} en parallèle${since(r.ms)}`
          : r.kind === 'agent' && r.status === 'done' && r.aborted ? `${r.aborted} interrompu${r.aborted > 1 ? 's' : ''} · ${meta}` : meta
        row += `<text x="${ix + 18}" y="${cy + 5}" class="${cls}">${esc(label)}</text>` +
          `<text x="${bx + bw - 12}" y="${cy + 4}" class="meta${r.status === 'run' ? ` live t-${b}` : ''}" text-anchor="end">${metaRow}</text>`
        out += `<g>${grows ? cascade(0.3 + 0.12 * i) : ''}${row}</g>`
        by += BOX + GAP
      })
    }
    out += `</g>`
    if (open && BRICKS.findIndex(([x]) => x === b) > BRICKS.findIndex(([x]) => x === open)) after += out
    else before += out
    if (grows) grow = h - HEAD
    prevBottom = y + h
    prevReached = reached
    y += h + 26
  }

  // les sous-agents qui moulinent, au-dessus du coût
  const sw = m.swarm
  if (sw.running.length) {
    const shown = sw.running.slice(0, 5)
    const sh = 52 + shown.length * 30 + (sw.running.length > shown.length ? 18 : 0) + 6
    let card = `<g transform="translate(10 ${y - 4})"><rect width="${W - 20}" height="${sh}" rx="18" class="swarm"/>` +
      spinner(32, 26, 11, '#8b5cf6', 3.5, 1.1) +
      `<text x="54" y="31" class="sw">${sw.running.length} sous-agent${sw.running.length > 1 ? 's' : ''} tourne${sw.running.length > 1 ? 'nt' : ''}</text>` +
      `<text x="${W - 34}" y="31" class="meta" text-anchor="end">pic ${sw.peak}${sw.done ? ` · ${sw.done} fini${sw.done > 1 ? 's' : ''}` : ''}</text>`
    shown.forEach((a, i) => {
      const ay = 62 + i * 30
      card += spinner(32, ay, 6, '#8b5cf6', 2, 0.8 + 0.15 * i) +
        `<text x="48" y="${ay + 4}" class="an">${esc(cut(a.name.replace(/^kwa:/, ''), 18))}</text>` +
        `<text x="${W - 34}" y="${ay + 4}" class="meta" text-anchor="end">${esc(cut(a.task, live ? 22 : 30))}${live ? `${a.task ? ' · ' : ''}${duration(a.ms)}` : ''}</text>`
    })
    if (sw.running.length > shown.length) card += `<text x="48" y="${62 + shown.length * 30}" class="meta">et ${sw.running.length - shown.length} de plus</text>`
    after += card + `</g>`
    y += sh + 12
  } else if (sw.peak) {
    // tout est revenu : une ligne de bilan
    after += `<text x="16" y="${y + 8}" class="meta">${sw.done} sous-agent${sw.done > 1 ? 's' : ''} lancé${sw.done > 1 ? 's' : ''}, jusqu'à ${sw.peak} en parallèle</text>`
    y += 22
  }

  // la carte du coût et du contexte
  const cardY = y - 4
  if (card === true) {
    after += `<g transform="translate(10 ${cardY})"><rect width="${W - 20}" height="112" rx="18" class="card"/>` +
      ringMarkup(contextPercent(u), intro, 58, 56) +
      `<text x="112" y="40" class="cost">${u?.usd != null ? money(u.usd) : '—'}</text>` +
      `<text x="112" y="62" class="meta">coût de la session · ${duration(sessionMs)}</text>` +
      `<text x="112" y="82" class="meta">contexte ${u?.tokens != null ? `${kilo(u.tokens)} / ${kilo(u.window)} jetons` : 'inconnu'}</text></g>`
  } else if (card === 'context') {
    // la carte du contexte seule : elle ne dépend que du pourcentage entier, le schéma reste donc stable
    const pct = contextPercent(u)
    const p = pct == null ? null : Math.round(pct)
    const say = p == null ? 'inconnu' : p < 50 ? 'de la place' : p < 80 ? 'penser à /compact bientôt' : 'à compacter ou passer le relais'
    after += `<g transform="translate(10 ${cardY})"><rect width="${W - 20}" height="112" rx="18" class="card"/>` +
      ringMarkup(p, intro, 58, 56) +
      `<text x="112" y="44" class="sw">Fenêtre de contexte</text>` +
      `<text x="112" y="66" class="meta">${p == null ? 'remplissage inconnu' : `${p} % utilisés`}</text>` +
      `<text x="112" y="86" class="meta">${say}</text></g>`
  }
  // pendant le dépliage, ce qui suit la brique ouverte part de sa place d'avant et descend avec elle
  const slide = grow ? `<animateTransform attributeName="transform" type="translate" from="0 ${-grow}" to="0 0" dur="${MORPH}s"${begin} ${EASE} fill="freeze"/>` : ''

  const H = card ? cardY + 124 : y
  const style = `<style>
text{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;fill:#18181b}
.title{font-size:18px;font-weight:700}.bh{font-size:13px;font-weight:700;letter-spacing:.06em;text-transform:uppercase}
.num{font-size:12px;font-weight:700}.num.on{fill:#fff}.wl{font-size:11px;font-weight:600;fill:#71717a}.wl.on{font-weight:800}
.sn{font-size:14px;font-weight:500}.now{font-weight:700}.dim{opacity:.5}.soft{opacity:.7}
.meta{font-size:12px;fill:#71717a}.live{font-weight:600}
.cost{font-size:26px;font-weight:750}.pct{font-size:15px;font-weight:700}
.frame{fill:none;stroke-width:1.5}.frame.open{stroke-width:2}.box{fill:#ffffff;stroke:#d4d4d8;stroke-width:1.5}.box.off{stroke-dasharray:4 4;stroke:#d4d4d8}
.ar{stroke-width:2}.ar.on{stroke:#10b981}.ar.off{stroke:#d4d4d8;stroke-dasharray:3 4}.ar.run{stroke-dasharray:6 6}
.tip{fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}.tip.on{stroke:#10b981}.tip.off{stroke:#d4d4d8}
.hollow{fill:none;stroke-width:2}.tick{fill:none;stroke:#fff;stroke-width:2.2;stroke-linecap:round;stroke-linejoin:round}
.card{fill:#f4f4f5;stroke:#e4e4e7}
.t-cadrer{fill:#4338ca}.t-faire{fill:#0369a1}.t-prouver{fill:#047857}.t-relire{fill:#7e22ce}.t-livrer{fill:#c2410c}.t-capitaliser{fill:#a16207}.swarm{fill:#8b5cf6;fill-opacity:.08;stroke:#8b5cf6;stroke-opacity:.45;stroke-width:1.5}
.sw{font-size:15px;font-weight:700}.an{font-size:13.5px;font-weight:600}.track{fill:none;stroke:#e4e4e7;stroke-width:10}
@media (prefers-color-scheme: dark){text{fill:#fafafa}.meta{fill:#a1a1aa}.wl{fill:#a1a1aa}.box{fill:#18181b;stroke:#3f3f46}
.box.off{stroke:#3f3f46}.ar.off{stroke:#3f3f46}.tip.off{stroke:#3f3f46}.card{fill:#18181b;stroke:#3f3f46}.track{stroke:#3f3f46}
.t-cadrer{fill:#818cf8}.t-faire{fill:#38bdf8}.t-prouver{fill:#34d399}.t-relire{fill:#c084fc}.t-livrer{fill:#fb923c}.t-capitaliser{fill:#facc15}}
</style>`
  return {
    width: W, height: H,
    source: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}">${style}${head}${before}<g>${slide}${after}</g></svg>`,
  }
}
