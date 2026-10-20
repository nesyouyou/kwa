import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register, Timer } from 'claude-code'

import type { Brick, Live, Step, Usage } from '../types'
import { BRICK_OF, BRICKS, classify, duration, fromJournal, guardBrick, guardOf, isOver, kilo, model, money, openBrick, svg } from './workflow'

// Rien de ce mod n'entre dans le contexte du modèle : il lit les événements et dessine, sans réécrire ni le prompt,
// ni le texte des skills, ni celui des sous-agents.
const steps = atom({ plugin: 'kwa-activity', key: 'steps' } as const, [])
const first = atom({ plugin: 'kwa-activity', key: 'first' } as const, null)
const usage = atom({ plugin: 'kwa-activity', key: 'usage' } as const, null)
const frame = atom({ plugin: 'kwa-activity', key: 'frame' } as const, 0)
// une fois par seconde tant qu'une étape tourne : les chronomètres natifs du Mod (frame, 8 fois par seconde, sert au terminal)
const beat = atom({ plugin: 'kwa-activity', key: 'beat' } as const, 0)
const isHidden = atom({ plugin: 'kwa-activity', key: 'isHidden' } as const, false)
const live = atom({ plugin: 'kwa-activity', key: 'live' } as const, null)
const touched = atom({ plugin: 'kwa-activity', key: 'touched' } as const, [])
const sid = atom({ plugin: 'kwa-activity', key: 'sid' } as const, null)
const branch = atom({ plugin: 'kwa-activity', key: 'branch' } as const, null)

const PANE = 'kwa-progress'
const KEEP = 200
const SPIN = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']

let tick: Timer | null = null
let poll: Timer | null = null
let seq = 0
// Les commandes de vérification de la politique du projet, lues au démarrage : une commande qui en relève est Prouver.
let verify: string[] = []
// Les agents déjà revenus : un turn.complete peut arriver avant que agent.spawn ait écrit l'étape.
const returned = new Set<string>()
// Par surface : la brique dessinée ouverte et l'instant où l'on y est entré, pour jouer le dépliage une fois.
const unfold = new Map<string, { brick: Brick | null; at: number }>()
// Lectures du journal faites pour la session en cours : la branche peut ne pas y être encore au tout premier relevé.
let journalReads = 0

const id = (prefix: string, now: number) => `${prefix}${now}-${++seq}`

// Tant qu'une étape tourne, l'indicateur du terminal tourne ; il s'arrête dès que tout est revenu.
async function animate($: EngineInterface) {
  if (tick) return
  let ticks = 0
  tick = $.clock.every(120, async () => {
    if (!(await read($, steps)).some(s => s.endedAt === null)) {
      tick?.cancel()
      tick = null
    }
    await update($, frame, n => (n + 1) % 1000)
    if (++ticks % 8 === 0 || !tick) await update($, beat, n => (n + 1) % 100000)
  })
}

// Sans surface attachée (session lancée avant Desktop ou le terminal), l'ouverture peut échouer : le mod continue,
// et le relevé périodique la retente tant que le panneau n'existe pas et que la personne ne l'a pas fermé.
async function openPane($: EngineInterface): Promise<{ isPlaced: boolean }> {
  try {
    return await $.ui.open({ id: PANE, title: 'Kwa · workflow' })
  } catch {
    return { isPlaced: false }
  }
}

const forget = ($: EngineInterface) => {
  returned.clear()
  unfold.clear()
  return Promise.all([update($, steps, () => []), update($, first, () => null), update($, live, () => null), update($, touched, () => [])])
}

// Le journal d'activité de la session, écrit par les hooks de Kwa (module memory) dans le dépôt principal ; null
// sans Kwa, sans module memory ou avant sa première ligne.
async function readJournal($: EngineInterface, session: string): Promise<string | null> {
  const root = (await $.session.repo())?.root ?? (await $.session.root())
  const dir = `${root}/.claude/kwa/local/activity`
  const name = `-${session.replace(/[^A-Za-z0-9_-]/g, '').slice(0, 64)}.jsonl`
  const f = (await $.fs.list(dir)).find(x => x.kind === 'file' && x.name.endsWith(name))
  return f ? String(await $.fs.read(`${dir}/${f.name}`)) : null
}

// Un /clear continue le processus sous une autre session, sans session.start : l'état du Mod la suivrait. Le relevé
// voit l'identifiant changer, oublie l'ancienne et lit le journal de la nouvelle. Le journal rend aussi ce qui
// précède le Mod (session reprise, Mod installé en cours de route) et la branche ; il n'est relu que tant que la
// branche manque, trois fois au plus : le direct vient des événements, pas du fichier.
async function syncJournal($: EngineInterface) {
  const now = await $.session.id()
  const prev = await read($, sid)
  if (prev !== now) {
    await update($, sid, () => now)
    journalReads = 0
    if (prev !== null) await Promise.all([forget($), update($, branch, () => null)])
  }
  if ((await read($, branch)) !== null || journalReads >= 3) return
  journalReads++
  const text = await readJournal($, now)
  if (text === null) return
  const r = fromJournal(text)
  await update($, branch, b => b ?? r.branch)
  if (r.steps.length && !(await read($, steps)).length) {
    await update($, steps, () => r.steps.slice(-KEEP))
    await update($, first, f => f ?? r.first)
  }
  if (r.touched.length) await update($, touched, l => (l.length ? l : r.touched))
}

async function refresh($: EngineInterface) {
  // sans journal lisible (pas de Kwa, dossier absent), le Mod suit la session en direct, comme avant
  await syncJournal($).catch(() => undefined)
  if (!(await read($, isHidden)) && !(await $.ui.panes()).some(p => p.id === PANE)) await openPane($)
  const u = await $.session.usage()
  const next: Usage = { usd: u.cost?.usd ?? null, tokens: u.context.tokens ?? null, window: u.context.window, percent: u.context.percent ?? null }
  await update($, usage, prev => (prev && prev.usd === next.usd && prev.tokens === next.tokens ? prev : next))
  // rattrapage : un agent qui ne reviendra jamais par turn.complete (distant, tué) est clos d'après la liste du moteur
  const list = await read($, steps)
  if (!list.some(s => s.kind === 'agent' && s.endedAt === null)) return
  const live = new Map((await $.agent.list()).map(a => [a.id, a.status]))
  const now = await $.clock.now()
  await update($, steps, l => l.map(s => {
    if (s.kind !== 'agent' || s.endedAt !== null) return s
    const st = live.get(s.id)
    if (!isOver(s, st, now)) return s
    // un agent de workflow clos faute de nouvelles a un sort inconnu : il n'est pas montré comme réussi
    return { ...s, endedAt: now, isAborted: st === 'killed' || st === 'failed' || (st === undefined && !!s.viaWorkflow) }
  }))
}

const isPlaced = async ($: EngineInterface) => (await $.ui.panes()).some(p => p.id === PANE && p.isPlaced)

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({ name: 'kwa-activity', description: 'Afficher le Mod Kwa (workflow et coût), ou le masquer' })
    try {
      const policy = JSON.parse(await $.fs.read('.claude/kwa.policy.json'))
      verify = Array.isArray(policy?.verify?.commands) ? policy.verify.commands.filter((c: unknown) => typeof c === 'string') : []
    } catch {
      verify = []  // pas de politique Kwa : la reconnaissance des tests se fait sur les commandes usuelles
    }
    await refresh($)
    poll ??= $.clock.every(4000, () => refresh($))
    if ((await read($, steps)).some(s => s.endedAt === null)) await animate($)
    return next(e)
  })

  on('command.run', { command: 'kwa-activity' }, async $ => {
    // un panneau en attente de place (terminal étroit) n'est pas visible : la commande l'affiche au lieu de le fermer
    if (await isPlaced($)) {
      await $.ui.close({ id: PANE })
      unfold.clear()  // le hook ui.close ne voit pas forcément la fermeture faite par ce mod lui-même
      await update($, isHidden, () => true)
      return { text: 'Mod Kwa fermé. /kwa-activity pour le rouvrir.' }
    }
    await update($, isHidden, () => false)
    const r = await openPane($)
    return { text: r.isPlaced ? 'Mod Kwa ouvert.' : 'Mod Kwa ouvert, en attente de place : le bandeau le remplace.' }
  })

  // Quelle que soit la façon de fermer le Mod (commande, marque, touche) : à la réouverture, l'anneau se remplit de
  // nouveau et rien ne se déplie pour une brique quittée entre-temps. Fermé à la main, il le reste
  // jusqu'à /kwa-activity ou la prochaine session (isHidden est un état de session).
  on('ui.close', async ($, e, next) => {
    if (e.id === PANE) {
      unfold.clear()
      if (e.origin.kind === 'person') await update($, isHidden, () => true)
    }
    return next(e)
  })

  on('skill.prompt', async ($, e, next) => {
    // seulement les skills de Kwa : /review, /init ou une skill locale « plan » ne sont pas des étapes Kwa
    const brick = e.skill.startsWith('kwa:') ? BRICK_OF[e.skill.slice(4)] : undefined
    if (brick) {
      const now = await $.clock.now()
      const name = `/${e.skill}`
      const s: Step = { id: id('s', now), kind: 'skill', name, task: '', brick, startedAt: now, endedAt: null, isAborted: false }
      await update($, first, f => f ?? name)
      // une skill qui démarre clôt la précédente : on suit une seule procédure à la fois
      await update($, steps, list => [...list.map(x => (x.kind === 'skill' && x.endedAt === null ? { ...x, endedAt: now } : x)), s].slice(-KEEP))
      await animate($)
    }
    return next(e)
  })

  on('agent.spawn', async ($, e, next) => {
    const result = await next(e)
    if (result.agentId) {
      const now = await $.clock.now()
      const list = await read($, steps)
      const last = [...list].reverse().find(x => x.kind === 'skill')
      const brick: Brick = /review/.test(e.subagentType) ? 'relire' : last?.brick ?? 'faire'
      const done = returned.delete(result.agentId)
      const a: Step = { id: result.agentId, kind: 'agent', name: e.subagentType, task: e.description, brick, startedAt: now, endedAt: done ? now : null, isAborted: false, viaWorkflow: !!e.workflow }
      await update($, steps, l => [...l.filter(x => x.id !== a.id), a].slice(-KEEP))
      await animate($)
    }
    return result
  }).catch(($, e, next) => next(e)) // ce mod observe seulement : une erreur ici ne doit jamais bloquer un sous-agent

  // Un refus d'un garde de Kwa (« Kwa — … ») devient une étape rouge du schéma.
  on('tool.call', async ($, e, next) => {
    const r = await next(e)
    const text = r.deny ?? (r.isError ? r.text : undefined)
    if (text && text.includes('Kwa —')) {
      const now = await $.clock.now()
      const name = guardOf(text)
      const last = [...(await read($, steps))].reverse().find(x => x.kind === 'skill')
      const brick = guardBrick(name, last?.brick)
      await update($, steps, l => [...l, { id: id('g', now), kind: 'garde' as const, name, task: '', brick, startedAt: now, endedAt: now, isAborted: false }].slice(-KEEP))
      return r
    }
    // ce que l'outil a fait (un refus n'a rien fait) : la ligne « en direct », et la brique touchée par le fil principal
    const seen = r.deny ? null : classify(String((e as { tool?: string }).tool ?? ''), e as unknown as Record<string, unknown>, verify)
    if (seen) {
      const now = await $.clock.now()
      const byAgent = !!e.agentId
      await update($, live, (): Live => ({ label: seen.label, brick: seen.brick, at: now, byAgent }))
      if (seen.brick && !byAgent) {
        const b = seen.brick
        await update($, touched, l => (l[l.length - 1] === b ? l : [...l.filter(x => x !== b), b]))
      }
    }
    return r
  }).catch(($, e, next) => next(e)) // observer seulement : ne jamais bloquer un outil

  on('turn.complete', async ($, e, next) => {
    const now = await $.clock.now()
    const list = await read($, steps)
    if (e.agentId && !list.some(x => x.id === e.agentId)) {
      returned.add(e.agentId)
      if (returned.size > 50) returned.delete(returned.values().next().value!)
    }
    await update($, steps, l => l.map(x => {
      if (x.endedAt !== null) return x
      if (e.agentId ? x.id === e.agentId : x.kind === 'skill') return { ...x, endedAt: now, isAborted: e.isAborted }
      return x
    }))
    await refresh($)
    return next(e)
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const list = await read($, steps)
    const u = await read($, usage)
    // recommencer, c'est aussi ne plus reprendre l'historique du journal
    const reset = () => { journalReads = 3; return forget($) }
    const t = await read($, touched)
    const act = await read($, live)
    // la dernière action, dite en une ligne : ce qu'elle a fait, par qui, il y a combien de temps
    const liveLine = (now: number) => act ? `${act.byAgent ? 'un sous-agent ' : ''}${act.label} · il y a ${duration(now - act.at)}` : null
    if (e.surface === 'desktop' || e.surface === 'mobile') {
      const { Box, Svg, Button } = $.ui.resolve(e)
      const now = await $.clock.now()
      const started = (await $.session.usage()).startedAt
      const m = model(list, now, (await read($, first)) ?? undefined, { touched: t, current: t[t.length - 1] ?? null }, await read($, branch))
      const open = openBrick(m)
      const seen = unfold.get(e.surface)
      if (!seen || seen.brick !== open) unfold.set(e.surface, { brick: open, at: now })
      await read($, beat)  // redessin chaque seconde tant qu'une étape tourne : seuls les textes natifs changent
      // Le schéma ne dépend que des étapes (ni chronomètre, ni coût) : son SVG reste identique d'un rendu à l'autre et
      // son cadre ne se recharge pas. Ce qui bouge tout le temps est dessiné en éléments natifs, mis à jour en place.
      const d = svg(m, u, now - started, { unfoldAgo: seen && open ? now - unfold.get(e.surface)!.at : null, intro: !seen, live: false, card: 'context' })
      const running = list.filter(x => x.endedAt === null)
      const { Text } = $.ui.resolve(e)
      // collé en haut du panneau : sans cela, un dessin plus court que le panneau y est centré verticalement
      return (
        <Box flexDirection="column" flexGrow={1} justifyContent="flex-start" alignItems="center" alignSelf="flex-start" width="100%" height="100%">
          <Svg key="flow" source={d.source} width={d.width} height={d.height} isInteractive
            alt={`${m.title} : ${m.rows.filter(x => x.status === 'done').length} étapes faites sur ${m.rows.length}`} />
          {act && (
            <Text key="now" wrap="truncate">
              <Text color="claude">◆ En direct </Text>
              <Text dimColor>{liveLine(now)}</Text>
            </Text>
          )}
          {running.length > 0 && (
            <Box key="live" flexDirection="column" width={d.width}>
              {running.slice(0, 6).map(x => (
                <Text key={x.id} wrap="truncate">
                  <Text color="claude">● </Text>
                  <Text bold>{x.kind === 'agent' ? x.name.replace(/^kwa:/, '') : x.name}</Text>
                  <Text dimColor>{x.task ? ` · ${x.task}` : ''} · en cours depuis {duration(now - x.startedAt)}</Text>
                </Text>
              ))}
            </Box>
          )}
          <Box key="cost" flexDirection="column" width={d.width}>
            <Text bold>{u?.usd != null ? money(u.usd) : '—'} <Text dimColor>coût de la session · {duration(now - started)}</Text></Text>
            <Text dimColor>contexte {u?.tokens != null ? `${kilo(u.tokens)} / ${kilo(u.window)} jetons` : 'inconnu'}</Text>
          </Box>
          {list.length > 0 && <Button key="reset" label="Recommencer le suivi" onPress={reset} />}
        </Box>
      )
    }
    const { Box, Text, Button } = $.ui.resolve(e)
    const n = await read($, frame)
    const now = await $.clock.now()
    const current = list.length ? list[list.length - 1]!.brick : null
    const at = current ? BRICKS.findIndex(([b]) => b === current) : -1
    const agents = list.filter(x => x.kind === 'agent' && x.endedAt === null).length

    return (
      <Box flexDirection="column">
        <Text>
          <Text bold>{u?.usd != null ? money(u.usd) : '—'}</Text>
          <Text dimColor> coût de la session</Text>
        </Text>
        {u?.tokens != null && (
          <Text dimColor>
            contexte {u.percent != null ? `${Math.round(u.percent)} %` : ''} ({kilo(u.tokens)} / {kilo(u.window)})
          </Text>
        )}
        {agents > 0 && <Text color="claude">{SPIN[n % SPIN.length]} {agents} sous-agent{agents > 1 ? 's' : ''} en cours</Text>}
        {act && <Text wrap="truncate"><Text color="claude">◆ </Text><Text dimColor>{liveLine(now)}</Text></Text>}
        <Text> </Text>
        {BRICKS.map(([b, label], i) => {
          const mine = list.filter(x => x.brick === b)
          const running = mine.some(x => x.endedAt === null)
          const glyph = running ? SPIN[n % SPIN.length] : mine.length ? '●' : i < at ? '–' : '○'
          const color = running ? 'claude' : mine.length ? 'success' : undefined
          return (
            <Box key={b} flexDirection="column">
              <Text wrap="truncate">
                <Text color={color}>{glyph} </Text>
                <Text bold={b === current} dimColor={!mine.length}>{i + 1}. {label}</Text>
                {!mine.length && i < at && <Text dimColor>  passée</Text>}
              </Text>
              {mine.map(x => {
                const icon = x.endedAt === null ? SPIN[n % SPIN.length] : x.isAborted || x.kind === 'garde' ? '✕' : '✓'
                const time = duration((x.endedAt ?? now) - x.startedAt)
                return (
                  <Text key={x.id} wrap="truncate">
                    <Text dimColor>   </Text>
                    <Text color={x.endedAt === null ? 'claude' : x.isAborted || x.kind === 'garde' ? 'error' : 'success'}>{icon} </Text>
                    <Text>{x.kind === 'agent' ? `↳ ${x.name}` : x.name}</Text>
                    <Text dimColor>{x.task ? ` · ${x.task}` : ''} · {time}</Text>
                  </Text>
                )
              })}
            </Box>
          )
        })}
        <Text> </Text>
        {list.length > 0 && <Button key="reset" label="Recommencer le suivi" onPress={reset} />}
      </Box>
    )
  })

  // Secours : quand le panneau ne peut pas s'afficher, une ligne au-dessus du prompt dit l'essentiel.
  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const list = await read($, steps)
    if (e.props.hasSurvey || (await read($, isHidden)) || !list.length || (await isPlaced($))) return next(e)
    const { Text } = $.ui.resolve(e)
    const last = list[list.length - 1]!
    const label = BRICKS.find(([b]) => b === last.brick)![1]
    const running = list.filter(x => x.kind === 'agent' && x.endedAt === null).length
    const u = await read($, usage)
    return (
      <Text wrap="truncate">
        <Text color="claude">◆ </Text>
        <Text bold>{label}</Text>
        <Text dimColor> · {last.name}{running ? ` · ${running} sous-agent${running > 1 ? 's' : ''} en cours` : ''}{u?.usd != null ? ` · ${money(u.usd)}` : ''}</Text>
      </Text>
    )
  })
}
