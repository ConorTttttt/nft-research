import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[2] / "phase3/integration-prototype")
)
from archive_io import encode
from grant import Profile, context, terminal_message
from lab import Lab, key, pub, slot
from protocol import receipt

out = Path(sys.argv[1])
k = key()
p = Profile(pub(k))
with Lab(7, 5, 2, anchor_for=p.anchor) as lab:
    proposal = lab.make(0)
    cert = receipt(proposal, lab.votes(range(5), proposal), 0)
    g = p.commitment(lab.config, slot(0), cert)
    evidence = ("paid", k.sign(terminal_message(g, "paid")).hex())
    (out / "p3").write_bytes(encode(p, lab.config, slot(0), cert, evidence))
    (out / "root3").write_bytes(context(lab.config))
