"""Validate sourced historical names and emit the eight-byte-name input table.

Original project work: djultra64. No original game data is embedded here.
"""
import argparse,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'config/rosters/real-names-1999-2000.json'
OUTPUT=ROOT/'src/runtime/pal_real_names_data.inc'
def generate(data):
 if data['schemaVersion']!=1 or data['revision']!='iss2000-pal-en-de-rev0':raise ValueError('Unsupported roster identity')
 players=data['players']
 if len(players)!=106*22:raise ValueError('A complete 106 by 22 factory table is required')
 for i,p in enumerate(players):
  if(p['teamId'],p['slot'])!=divmod(i,22):raise ValueError('Factory names must be complete and ordered')
  if not re.fullmatch(r'[A-Za-z0-9 .]{1,8}',p['displayName'])or not p['displayName'].strip():raise ValueError('Name exceeds the verified Latin encoding')
  if not p['fullName']or not p['source'].startswith('https://')or not p['rosterSources']or any(not u.startswith('https://')for u in p['rosterSources']):raise ValueError('Historical name evidence is required')
  if p['periodException']!=not_1999_2000(p['documentedYears']):raise ValueError('Period exception must match the evidence years')
  if p['teamId']>=100:
   original=players[p['originTeamId']*22+p['originSlot']]
   if(p['displayName'],p['fullName'],p['source'])!=(original['displayName'],original['fullName'],original['source']):raise ValueError('Special-team names must follow verified original provenance')
 for team in range(100):
  rows=players[team*22:(team+1)*22]
  if len({p['source']for p in rows})!=22 or len({p['displayName'].lower()for p in rows})!=22:raise ValueError('Duplicate player or ambiguous display within a national team')
 if sum(p['periodException']for p in players[:2200])!=data['ordinaryPeriodExceptions']:raise ValueError('Incorrect exception count')
 return ('// Generated factual names; original project work: djultra64.\n// Regenerate with tools.generate_pal_real_names; sources are in config/rosters.\n'+''.join(json.dumps(p['displayName'])+',\n'for p in players)).encode()
def not_1999_2000(years):
 if not years or any(type(y)is not int or y<1900 or y>2002 for y in years):raise ValueError('Invalid historical evidence years')
 return not any(y in(1999,2000)for y in years)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data',type=Path,default=DATA);p.add_argument('--output',type=Path,default=OUTPUT);p.add_argument('--check',action='store_true');a=p.parse_args();generated=generate(json.loads(a.data.read_text()))
 if a.check:
  if not a.output.is_file()or a.output.read_bytes()!=generated:raise SystemExit('Historical name table is stale')
 else:a.output.write_bytes(generated)
 print('Verified 2332 factory names; original attributes and user-created records remain outside this table.')
