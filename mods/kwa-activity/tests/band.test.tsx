import { expect, mock, test } from 'claude-code/testing'
import type { On } from 'claude-code'

// Ce qui tient lieu du moteur sous le mod : horloge, texte des skills, dessin par défaut, panneau, usage de la session.
function engine(on: On, placed = true, extra: { panes?: unknown[]; agents?: unknown[]; noSurface?: () => boolean } = {}) {
  const clock = mock.clock(on)
  on('skill.prompt', ($, e) => ({ text: e.text }))
  on('ui.render', ($, e) => { const { Box } = $.ui.resolve(e); return <Box key="engine" /> })
  on('command.register', ($, e) => ({ value: { command: e.name } }))
  on('turn.complete', ($, e) => ({ text: e.answer }))
  on('ui.open', () => {
    if (extra.noSurface?.()) throw new Error('no-surface: no surface is attached ($.session.surfaces() is empty)')
    return { value: placed ? { isPlaced: true } : { isPlaced: false, reason: 'narrow' } } as never
  })
  on('ui.panes', () => ({ value: extra.panes ?? [] }) as never)
  on('agent.list', () => ({ value: extra.agents ?? [] }) as never)
  on('session.start', ($, e) => ({ cwd: e.cwd }))
  on('ui.close', () => { closed.n++; return { value: undefined } })
  on('session.usage', () => ({ value: { startedAt: 0, context: { tokens: 76000, window: 200000, percent: 38 }, rateLimits: [], cost: { usd: 0.42 } } }))
  return clock
}

const closed = { n: 0 }
const PANE = {
  plugin: 'kwa-activity', component: 'Pane', requestId: 'kwa-progress',
  props: { title: 'Kwa · workflow', isFocused: false, bodyColumns: 40, placement: 'dock', scroll: { offset: 0, bodyRows: 30 }, view: {} },
} as const
const BAND = {
  plugin: 'kwa-activity', component: 'AbovePrompt',
  props: { hasSurvey: false, isWorking: true, maxRows: 10, bodyColumns: 100, scroll: { offset: 0, bodyRows: 10 }, view: {} },
} as const
const spawn = { tool_use_id: 't1', prompt: 'Relis.', description: 'relire le diff', subagentType: 'kwa:reviewer' }

test('le panneau suit les briques, les skills, les sous-agents et le coût', async ($, on) => {
  engine(on)
  on('agent.spawn', () => ({ model: 'sonnet', agentId: 'a1' }))
  await $.session.start({ source: 'startup', cwd: '/tmp', surface: 'terminal', isInteractive: true } as Parameters<typeof $.session.start>[0])
  await $.skill.prompt({ skill: 'kwa:debug', text: 'x' })
  await $.skill.prompt({ skill: 'kwa:review', text: 'x' })
  await $.agent.spawn(spawn as Parameters<typeof $.agent.spawn>[0])

  const desk = await $.ui.mount({ ...PANE, surface: 'desktop' })
  const drawing = await desk.find({ type: 'Svg' })
  expect(drawing).toBeDefined()
  expect(JSON.stringify(drawing)).toContain('Corriger un bug')
  await desk.unmount()

  for (const surface of ['terminal'] as const) {
    const ui = await $.ui.mount({ ...PANE, surface })
    expect(await ui.find({ type: 'Text', text: /0,42 \$/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /38 %/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /1\. Cadrer/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /\/kwa:debug/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /2\. Faire/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /passée/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /↳ kwa:reviewer/ })).toBeDefined()
    await ui.unmount()
  }

  await $.turn.complete({ agentId: 'a1', answer: 'ok', durationMs: 1000, isAborted: false, turnId: 'x', reason: 'answer' } as Parameters<typeof $.turn.complete>[0])
  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  expect(await ui.find({ type: 'Text', text: /✓ / })).toBeDefined()
  await ui.press({ key: 'reset' })
  expect(await ui.find({ type: 'Text', text: /\/kwa:debug/ })).toBeUndefined()
  await ui.unmount()
})

test('sans place pour le panneau, le bandeau prend le relais ; le texte des skills reste intact', async ($, on) => {
  engine(on, false)
  await $.session.start({ source: 'startup', cwd: '/tmp', surface: 'terminal', isInteractive: true } as Parameters<typeof $.session.start>[0])
  const out = await $.skill.prompt({ skill: 'kwa:tdd', text: 'Test d’abord.' })
  expect(out.text).toBe('Test d’abord.')
  const band = await $.ui.mount({ ...BAND, surface: 'terminal' })
  expect(await band.find({ type: 'Text', text: /Prouver/ })).toBeDefined()
  expect(await band.find({ type: 'Text', text: /0,42 \$/ })).toBeDefined()
  await band.unmount()
})

test('une skill hors Kwa est ignorée ; la commande affiche un panneau en attente au lieu de le fermer', async ($, on) => {
  engine(on, false, { panes: [{ id: 'kwa-progress', title: 'Kwa · workflow', isPlaced: false }] })
  closed.n = 0
  await $.session.start({ source: 'startup', cwd: '/tmp', surface: 'terminal', isInteractive: true } as Parameters<typeof $.session.start>[0])
  await $.skill.prompt({ skill: 'review', text: 'x' })
  const band = await $.ui.mount({ ...BAND, surface: 'terminal' })
  expect(await band.find({ type: 'Text', text: /Relire/ })).toBeUndefined()
  await band.unmount()
  const r = await $.command.run({ command: 'kwa-activity', args: '' } as Parameters<typeof $.command.run>[0])
  expect(closed.n).toBe(0)
  expect(JSON.stringify(r)).toContain('ouvert')
})

test('un sous-agent que le moteur dit fini est clos, même sans fin de tour', async ($, on) => {
  engine(on, true, { agents: [{ id: 'r1', description: 'x', type: 'kwa:reviewer', status: 'killed' }] })
  on('agent.spawn', () => ({ model: 'sonnet', agentId: 'r1' }))
  await $.session.start({ source: 'startup', cwd: '/tmp', surface: 'terminal', isInteractive: true } as Parameters<typeof $.session.start>[0])
  await $.skill.prompt({ skill: 'kwa:review', text: 'x' })
  await $.agent.spawn(spawn as Parameters<typeof $.agent.spawn>[0])
  // une fin de tour du fil principal relance le relevé, qui interroge la liste des agents
  await $.turn.complete({ answer: 'ok', durationMs: 1, isAborted: false, turnId: 'm', reason: 'answer' } as Parameters<typeof $.turn.complete>[0])
  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  expect(await ui.find({ type: 'Text', text: /sous-agent.* en cours/ })).toBeUndefined()
  expect(await ui.find({ type: 'Text', text: /✕ / })).toBeDefined()
  await ui.unmount()
})

test('un agent de workflow absent de la liste du moteur reste en cours', async ($, on) => {
  engine(on)
  on('agent.spawn', () => ({ model: 'sonnet', agentId: 'w1' }))
  await $.session.start({ source: 'startup', cwd: '/tmp', surface: 'terminal', isInteractive: true } as Parameters<typeof $.session.start>[0])
  await $.skill.prompt({ skill: 'kwa:review', text: 'x' })
  await $.agent.spawn({ ...spawn, workflow: { runId: 'r' } } as unknown as Parameters<typeof $.agent.spawn>[0])
  await $.turn.complete({ answer: 'ok', durationMs: 1, isAborted: false, turnId: 'm', reason: 'answer' } as Parameters<typeof $.turn.complete>[0])
  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
  expect(await ui.find({ type: 'Text', text: /1 sous-agent en cours/ })).toBeDefined()
  await ui.unmount()
})

test('le dépliage se joue par surface, à l\u2019entrée dans une nouvelle brique', async ($, on) => {
  engine(on)
  await $.session.start({ source: 'startup', cwd: '/tmp', surface: 'desktop', isInteractive: true } as Parameters<typeof $.session.start>[0])
  await $.skill.prompt({ skill: 'kwa:debug', text: 'x' })
  const src = async (surface: 'desktop' | 'mobile') => {
    const ui = await $.ui.mount({ ...PANE, surface })
    const s = JSON.stringify(await ui.find({ type: 'Svg' }))
    await ui.unmount()
    return s
  }
  expect(await src('desktop')).not.toContain('attributeName=\\"height\\"')   // premier rendu : pas de dépliage
  await $.skill.prompt({ skill: 'kwa:tdd', text: 'x' })
  expect(await src('desktop')).toContain('attributeName=\\"height\\"')       // entrée dans Prouver
  expect(await src('mobile')).not.toContain('attributeName=\\"height\\"')    // l'autre surface a son propre suivi
})

test('fermé par la commande, le Mod repart de zéro : l\u2019anneau se remplit de nouveau au rendu suivant', async ($, on) => {
  engine(on, true, { panes: [{ id: 'kwa-progress', title: 'Kwa · workflow', isPlaced: true }] })
  await $.session.start({ source: 'startup', cwd: '/tmp', surface: 'desktop', isInteractive: true } as Parameters<typeof $.session.start>[0])
  await $.skill.prompt({ skill: 'kwa:debug', text: 'x' })
  const src = async () => {
    const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
    const s = JSON.stringify(await ui.find({ type: 'Svg' }))   // la carte du contexte est dans le schéma
    await ui.unmount()
    return s
  }
  const ring = 'attributeName=\\"stroke-dasharray\\"'
  await src()
  expect(await src()).not.toContain(ring)                         // l'anneau ne se remplit qu'au premier rendu
  await $.command.run({ command: 'kwa-activity', args: '' } as Parameters<typeof $.command.run>[0])
  expect(await src()).toContain(ring)                             // rouvert : il se remplit de nouveau
})

test('sans surface au démarrage, le mod démarre quand même et rouvre son panneau au relevé suivant', async ($, on) => {
  let bare = true
  let opens = 0
  const clock = engine(on, true, { noSurface: () => { opens++; return bare } })
  await $.session.start({ source: 'startup', cwd: '/tmp', surface: 'terminal', isInteractive: true } as Parameters<typeof $.session.start>[0])
  expect(opens).toBe(1)
  // la commande est bien enregistrée malgré l'échec de l'ouverture
  const r = await $.command.run({ command: 'kwa-activity', args: '' } as Parameters<typeof $.command.run>[0])
  expect(JSON.stringify(r)).toContain('Mod Kwa')
  bare = false
  await clock.advance(4000)
  expect(opens).toBeGreaterThanOrEqual(3)   // l'ouverture du démarrage, celle de la commande, puis celle du relevé
})

test('le schéma ne change pas pendant qu\u2019une étape tourne : seuls les textes natifs avancent', async ($, on) => {
  const clock = engine(on)
  await $.session.start({ source: 'startup', cwd: '/tmp', surface: 'desktop', isInteractive: true } as Parameters<typeof $.session.start>[0])
  await $.skill.prompt({ skill: 'kwa:tdd', text: 'x' })
  const snap = async () => {
    const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
    const flow = JSON.stringify(await ui.find({ type: 'Svg' }))
    const live = await ui.find({ type: 'Text', text: /en cours depuis/ })
    await ui.unmount()
    return { flow, live: JSON.stringify(live) }
  }
  await snap()
  await clock.advance(2000)   // au-delà du dépliage : le schéma est stable
  const a = await snap()
  await clock.advance(5000)
  const b = await snap()
  expect(a.flow).toContain('Développer')      // le dessin est bien trouvé : sinon la comparaison ne prouverait rien
  expect(b.flow).toBe(a.flow)              // même SVG : son cadre ne se recharge pas, rien ne clignote
  expect(a.live).not.toBe(b.live)          // le chronomètre natif, lui, a avancé
  expect(a.flow).not.toContain('0,42 $')   // le coût n'est plus dans le schéma
  expect(a.flow).toContain('Fenêtre de contexte')   // la carte du contexte, elle, y reste
})

test('le Mod suit en direct ce que font les outils, même sans skill Kwa', async ($, on) => {
  engine(on)
  on('tool.call', { tool: 'Edit' }, () => ({ result: {}, text: 'ok' }) as never)
  on('tool.call', { tool: 'Bash' }, () => ({ result: {}, text: 'ok' }) as never)
  await $.session.start({ source: 'startup', cwd: '/tmp', surface: 'desktop', isInteractive: true } as Parameters<typeof $.session.start>[0])
  await $.tool.call({ tool: 'Edit', file_path: '/p/src/panier.py', old_string: 'a', new_string: 'b' } as never)
  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect(await ui.find({ type: 'Text', text: /modifie panier\.py/ })).toBeDefined()
  expect(JSON.stringify(await ui.find({ type: 'Svg' }))).toContain('frame open')   // une brique s'ouvre sans skill
  await ui.unmount()
  await $.tool.call({ tool: 'Bash', command: 'python3 -m unittest' } as never)
  const ui2 = await $.ui.mount({ ...PANE, surface: 'terminal' })
  expect(await ui2.find({ type: 'Text', text: /lance python3 -m unittest/ })).toBeDefined()
  await ui2.unmount()
})

test('le Mod reprend le journal de Kwa de sa session, et repart de zéro après un /clear', async ($, on) => {
  const clock = engine(on)
  let session = 's-old'
  const dir = '/repo/.claude/kwa/local/activity'
  const files: Record<string, string> = {
    's-old': [{ ts: 1, kind: 'session', branch: 'fix/14-panier' }, { ts: 2, kind: 'skill', name: 'kwa:debug' },
      { ts: 3, kind: 'agent', name: 'kwa:reviewer', target: 'relire' }].map(x => JSON.stringify(x)).join('\n'),
    's-new': JSON.stringify({ ts: 9, kind: 'session', source: 'clear', branch: 'feat/15-export' }),
  }
  on('session.id', () => ({ value: session }) as never)
  on('session.repo', () => ({ value: { root: '/repo', remote: null, internal: false, name: null } }) as never)
  on('fs.list', ($, e) => ({ value: e.path === dir ? Object.keys(files).map(k => ({ name: `2026-10-20-${k}.jsonl`, kind: 'file', size: 1, mtimeMs: 0, isLink: false })) : [] }) as never)
  on('fs.read', ($, e) => {
    const k = Object.keys(files).find(x => e.path === `${dir}/2026-10-20-${x}.jsonl`)
    if (!k) throw new Error('ENOENT')
    return { value: files[k] } as never
  })
  await $.session.start({ source: 'resume', cwd: '/repo', surface: 'desktop', isInteractive: true } as Parameters<typeof $.session.start>[0])
  const term = async () => {
    const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
    const out = { debug: await ui.find({ type: 'Text', text: /\/kwa:debug/ }), agent: await ui.find({ type: 'Text', text: /↳ kwa:reviewer/ }) }
    await ui.unmount()
    return out
  }
  const before = await term()
  expect(before.debug).toBeDefined()      // la skill d'avant la reprise
  expect(before.agent).toBeDefined()      // et le sous-agent, clos avec le journal
  session = 's-new'                       // /clear : même processus, autre session, sans session.start
  await clock.advance(4000)
  const after = await term()
  expect(after.debug).toBeUndefined()
  const desk = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect(JSON.stringify(await desk.find({ type: 'Svg' }))).toContain('feat/15-export')   // le workflow, d'après la branche
  await desk.unmount()
})
