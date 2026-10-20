"""Headless smoke test: play rounds through the generated pack."""
from __future__ import annotations
from pathlib import Path
from sim import Sim

ROOT = Path('/home/user/animacje13/build4/26.2')


def tick(sim, times=1):
    for _ in range(times):
        sim.call('tick')


def boot():
    sim = Sim(ROOT, seed=3)
    steve = sim.player('Steve')
    sim.sender = 'Steve'
    sim.call('load')
    sim.call('setup')
    return sim, steve


def report(label, sim, steve, **extra):
    print(f'{label:24} state={sim.score("#state","gti.var")} used={sim.score("#used","gti.var")} '
          f'left={sim.score("#left","gti.var")} revealed={sim.score("#revealed","gti.var")} '
          f'wins={steve.scores.get("gti.wins",0)} best={steve.scores.get("gti.best",0)}',
          ' '.join(f'{k}={v}' for k, v in extra.items()))


def main():
    sim, steve = boot()
    print('grid', sum(1 for e in sim.entities if 'gti.cell' in e.tags),
          'clicks', sum(1 for e in sim.entities if 'gti.click' in e.tags),
          'pips', sum(1 for e in sim.entities if 'gti.pip' in e.tags))

    # --- round 1: correct guess
    sim.call('start')
    tick(sim, 70)
    answer = sim.storage['gti:cfg']['answer']
    report('round live', sim, steve, answer=answer)
    steve.nbt['SelectedItem'] = {'id': answer}
    sim.set('Steve', 'gti_guess', 1)
    tick(sim, 1)
    report('after correct guess', sim, steve)
    tick(sim, 40)
    print('   curtain phase status:', sim.storage['gti:cfg']['status'])
    tick(sim, 110)
    report('after finale', sim, steve, status=sim.storage['gti:cfg']['status'])
    print('   board reset:', sum(1 for e in sim.entities if 'gti.cell' in e.tags and 'gti.open' not in e.tags))

    # --- round 2: manual host pick + clicks + wrong guess
    sim.call('data/set_id', {'id': 'diamond_sword'})
    print('host pick ->', sim.storage['gti:cfg']['answer'], 'art', sim.storage['gti:cfg']['art_key'])
    sim.call('start')
    tick(sim, 70)
    clicks = [e for e in sim.entities if 'gti.click' in e.tags and 'gti.open' not in e.tags]
    for i in range(3):
        clicks[i].nbt['interaction'] = 1.0
        sim.call('tick')
    report('after 3 clicks', sim, steve)
    steve.nbt['SelectedItem'] = {'id': 'minecraft:stone'}
    sim.set('Steve', 'gti_guess', 1)
    tick(sim, 1)
    report('after wrong guess', sim, steve, guesses=sim.score('#guesses', 'gti.var'))

    # --- round 3: attempt limit reached
    sim.set('#limit', 'gti.var', 4)
    sim.set('#used', 'gti.var', 4)
    sim.call('strip/refresh')
    sim.call('reveal/request')
    tick(sim, 1)
    report('limit reached', sim, steve)

    # --- settings / presets
    sim.call('cfg/apply', {'limit': '20', 'batch': '2', 'initial': '1', 'mode': 'auto', 'timer': '60', 'hints': '1'})
    print('settings ->', sim.storage['gti:cfg']['settings'], 'limit', sim.score('#limit', 'gti.var'),
          'timer', sim.score('#timer_sec', 'gti.var'))
    for preset in ('chill', 'normal', 'hard', 'default'):
        sim.call('preset/' + preset)
        print(f'  preset {preset:8} ->', sim.storage['gti:cfg']['settings'])

    # --- category pick
    sim.call('preset/default')
    sim.set('Steve', 'gti_pick', 1 + 3 * 10000 + 5)
    sim.call('tick')
    print('category pick ->', sim.storage['gti:cfg']['answer'], 'source', sim.score('#source', 'gti.var'))

    # --- stats dialog triggers
    sim.set('Steve', 'gti_stats', 1)
    tick(sim, 1)
    print('stats trigger ok, rounds', steve.scores.get('gti.rounds', 0))


if __name__ == '__main__':
    main()
