"""Check a funded cooperative control against the meaning of the release standing query."""
import json
import sys
from pathlib import Path
rows=[json.loads(line) for line in Path(sys.argv[1]).read_text().splitlines()]
reads={(r['reader'],r['after']):r['value'] for r in rows if r.get('step')=='park standing'}
records={r['step']:r['value'] for r in rows if 'step' in r}
terms=records['verified conditional grant']['terms']
for reader in ('p4-buyer','p4-progenitor'):
    parked=reads[reader,'create_parked_spend']['Parked']
    assert parked['amount']=={terms['unit']:terms['amount']}
    assert reads[reader,'create_receipt_from_rave']=='Unparked'
assert records['independent acceptance']['status']=='Pending'
print('Both readers observed Parked(10) followed by Unparked on a collected sale.')
