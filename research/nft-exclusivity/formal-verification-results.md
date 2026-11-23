# What was verified

Run `python3 formal-models/explore.py` and `python3 formal-models/failures.py`. Both use only the standard library. The first explores a finite transition relation by breadth-first search with duplicate-state elimination. The second constructs explicit schedules that falsify stronger claims. The unbounded paper argument and its hypotheses are in [mathematical results](mathematical-results.md).

**Single-input and product machines.** Each honest witness stores a mask of statements it has ever signed. One transition adds a previously unsigned proposal if its input set is disjoint from all different statements that witness signed. All parents in these machines are initially verified. A proposal is final if its honest mask count plus the Byzantine count reaches q. Counting all Byzantine votes from the start gives the adversary maximum power for safety. Every schedule of honest signature releases, including indefinitely delayed releases, is represented. Network buffers, client views, delivery fairness, cryptography, storage implementation and wall clocks are abstracted away. Repeated delivery changes no state.

| Model | Reachable states | Result |
|---|---:|---|
| 4/3/1, three proposals touching one whole-object guard | 64 | Only individual proposals can be final. |
| 4/3/1, assignments X, Y and a bundle XY | 125 | X and Y can both finish. XY cannot finish alongside either. |
| 7/5/2, two conflicting spends | 243 | No double certificate. |
| 7/4/2, two conflicting spends | Counterexample | Two honest signatures on A, two different honest signatures on B, two Byzantine signatures on each. |

The checker also enumerates all uniform quorum pairs for n up to eight and compares their minimum intersections with the inequality. The grant model has a previously fixed grant, two disconnected presentations and a set of allowed recipients. Its only transition presents an allowed child to a local observer. For a fixed recipient no incompatible outputs exist. Giving both presenters a free choice immediately yields B and C. The grant model assumes authentic setup, monotone release and the same child identity on every replay. Only release after grant is live if the condition is satisfiable and its evidence reaches the recipient.

**Failures.** In the rollback trace a hidden A is signed by {0,1,2,3,4}; {0,1} are Byzantine. One honest rollback at 2 enables B under {0,1,2,5,6}. In the epoch trace a fresh disjoint roster certifies B on the same predecessor. In the split-vote trace honest voters divide 3–2 and both Byzantine voters abstain. Neither digest can ever reach five even after partition healing. Rollback and arbitrary reconfiguration violate assumptions. Split voting is a liveness limitation within the stated model. The guard enumerator confirms three guards are necessary for the star with three leaves. These runs supply bounded evidence and diagnostic traces. No general machine-checked liveness or cryptographic proof is claimed.

A third script, `python3 formal-models/handoff.py`, explores 391 reachable states with three disjoint 4/3/1 rosters. The old input can choose either of two child rosters. Each new roster can authorise one of two competing grandchildren only after its own parent handoff is certified. At most one grandchild becomes final across both domains. This models complete proof availability to a potential new voter whenever a certificate exists, and arbitrary scheduling of its vote. It demonstrates a safe alternative to resetting an existing predecessor under fresh membership.
