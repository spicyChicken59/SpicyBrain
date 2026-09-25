#!/usr/bin/env python3
"""Deduplicate claim-to-source/section/content review; do not infer factual PASS.

--write refreshes the ledger; --check checks freshness. --require-complete is
an editorial closeout gate and fails while any new-module claim lacks review.
Earlier direct reads retain their provenance but are not automatically promoted
to claim-level verification by a URL classifier or a reachability probe.
"""
import argparse
import collections
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'docs/academy/CLAIM-REVIEW.json'


def build():
    reviews = json.loads((ROOT / 'docs/academy/CLAIM-REVIEWS.json').read_text())
    source_reviews = {r['url']: r for r in reviews['sources']}
    decisions = {r['id']: r for r in reviews['claims']}
    sources, claims, uses = {}, {}, collections.defaultdict(set)
    paths = [ROOT / 'content/courses/dbxfe/course.json']
    paths += sorted((ROOT / 'content/courses/dbxfe/modules').glob('*.json'))
    paths += sorted((ROOT / 'content/courses/dbxfe/lessons').glob('*.json'))
    paths += sorted((ROOT / 'content/teaching/dbxfe').glob('*.json'))
    for path in paths:
        data = json.loads(path.read_text())
        if not isinstance(data, dict):
            continue
        rel = path.relative_to(ROOT).as_posix()
        mid = data.get('moduleId') or data.get('module', {}).get('id')
        for s in data.get('sources', []):
            sources[s['id']] = {k: s.get(k) for k in ('id', 'url', 'reviewedEvidence', 'caveat', 'reviewedAt', 'reviewDate')}
        for c in data.get('claims', []):
            if c['kind'] != 'documented':
                continue
            if c['id'] in claims and claims[c['id']]['claim'] != c['description']:
                raise ValueError('Conflicting claim definitions: ' + c['id'])
            digest = hashlib.sha256(json.dumps(c, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
            unchanged = reviews['baselineClaimDigests'].get(c['id']) == digest
            claims[c['id']] = dict(id=c['id'], moduleId=mid,
                                   scope='retained-evidence' if unchanged else 'new-or-materially-changed',
                                   claim=c['description'], sourceIds=c['sourceIds'], definition=rel)
        def walk(obj, owner='root'):
            if isinstance(obj, dict):
                owner = obj.get('id', owner)
                for cid in obj.get('claimIds', []):
                    uses[cid].add(rel + '#' + owner)
                for value in obj.values():
                    if isinstance(value, (dict, list)):
                        walk(value, owner)
            elif isinstance(obj, list):
                for value in obj:
                    walk(value, owner)
        walk(data)
    rows = []
    for cid, c in sorted(claims.items()):
        decision = decisions.get(cid)
        refs = []
        for sid in c.pop('sourceIds'):
            s = sources[sid]
            review = source_reviews.get(s['url'])
            refs.append(dict(sourceId=sid, url=s['url'],
                             sections=review['sections'] if review else [],
                             reviewDate=review['reviewedAt'] if review else (s.get('reviewedAt') or s.get('reviewDate')),
                             method='direct-page-read' if review else 'historical-record-see-source',
                             evidenceRecord='docs/academy/CLAIM-REVIEWS.json' if review else c['definition']))
        c.update(sources=refs, affectedContent=sorted(uses[cid] | set((decision or {}).get('additionalAffectedContent', []))),
                 status=decision['status'] if decision else ('retained-prior-evidence' if c['scope']=='retained-evidence' else 'pending-claim-review'),
                 review=decision or None)
        rows.append(c)
    return dict(generatedBy='python scripts/academy-claim-review.py --write',
                rule='A direct page read is not automatically a verified claim. Explicit decisions bind a specific claim to inspected sections and affected content. Pending is incomplete work, not an assertion that access is blocked.',
                totals=dict(claims=len(rows), byStatus=dict(collections.Counter(r['status'] for r in rows))), claims=rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--require-complete', action='store_true')
    args = parser.parse_args()
    report = build()
    text = json.dumps(report, indent=1, ensure_ascii=False) + '\n'
    if args.write:
        OUT.write_text(text)
    print(json.dumps(report['totals']))
    if args.check and (not OUT.exists() or OUT.read_text() != text):
        raise SystemExit('Claim ledger is stale')
    if args.require_complete and any(r['status'] in ('pending-claim-review', 'partial') for r in report['claims']):
        raise SystemExit('G14 BLOCKED: unresolved claim-level review remains')


if __name__ == '__main__':
    main()
