"""Summarize private real-engine logs; unit-test fixtures are not game evidence.

Original project work: djultra64. Successful API presentation is not proof that
120 distinct frames reached a physical display. GPU capture changes performance.
"""
import argparse,json,statistics
from collections import defaultdict
from pathlib import Path

def analyze(events):
 renders=[e for e in events if e.get('event')=='render']
 presents=[e for e in events if e.get('event')=='present' and e.get('success') is True]
 displays=[e for e in events if e.get('event')=='display']
 groups=defaultdict(list)
 for e in renders:
  h=e.get('pixel_sha256','')
  if e.get('capture')=='gpu_readback' and e.get('matched') is True and len(h)==64 and all(c in '0123456789abcdef' for c in h):groups[e['workload']].append(e)
 distinct=[]
 for workload,frames in groups.items():
  weights={e['weight'] for e in frames};hashes={e['pixel_sha256'] for e in frames}
  if any(0<w<1 for w in weights) and len(weights)>1 and len(hashes)>1:distinct.append(workload)
 stamps=[e['time_us'] for e in presents if 'time_us' in e]
 intervals=[b-a for a,b in zip(stamps,stamps[1:]) if b>a]
 dls=[e for e in events if e.get('event')=='display_list']
 return dict(render_calls=len(renders),fractional_render_calls=sum(0<e.get('weight',1)<1 for e in renders),
  gpu_readbacks=sum(e.get('capture')=='gpu_readback' for e in renders),distinct_fractional_gpu_workloads=sorted(distinct),
  requested_rates_hz=sorted({e['requested_hz'] for e in displays}),detected_display_rates_hz=sorted({e['detected_hz'] for e in displays}),
  effective_render_rates_hz=sorted({e['target_hz'] for e in renders}),successful_present_calls=len(presents),
  median_present_interval_us=statistics.median(intervals) if intervals else None,
  tagged_model_groups=sum(e.get('model_groups',0) for e in dls),tagged_camera_groups=sum(e.get('camera_groups',0) for e in dls),
  missing_snapshot_tasks=sum(e.get('snapshot') is False for e in dls),
  physical_120hz_proven=False,limitations=['GPU readback affects frame timing and may cause skipped intermediates.','Different pixel hashes plus distinct weights in one matched workload demonstrate distinct GPU intermediates.','Presentation API success does not establish physical display scanout or 120 Hz acceptance.','Display-list group counts are asynchronous eligibility evidence, not pixel-to-task attribution.'])
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('log',type=Path);args=parser.parse_args()
 events=[json.loads(line) for line in args.log.read_text().splitlines() if line.strip()]
 print(json.dumps(analyze(events),indent=2))
if __name__=='__main__':main()
