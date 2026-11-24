# Decision candidates

| Candidate | Where conflicting choices meet | Progress condition | Limitation or falsifier |
|---|---|---|---|
| A. Per-title CEL, external commercial script | Every title successor requires its parent quorum | q reachable and willing on each choice | Paying before a discretionary final transfer exposes the buyer. A second round can stall after cash settles. |
| B. Versioned exclusive resources | Atomic certificate covers exact conflicting guards, including authority to create future burdens | Every consumed guard can participate in the same certificate | Disjoint committees require a joint protocol. Independent successful local votes do not form an atomic batch by themselves. |
| C. Agreement-native fixed destination | Initial commitment fixes parties and predicates. Both systems recognize the same terminal outcome | Terminal evidence plus the commitment can be retrieved | Executor-selected booleans and proofs of absence break determinism or uniqueness of the outcome. |
| D. Single joint state machine | Move both bearer instruments under one transactional authority before trading. One log entry updates title and cash | Joint authority and asset custody remain available | Requires an irreversible import and redemption boundary for native Unyt. A synthetic deposit-backed claim introduces custodian and backing risk. |
| E. Time-locked two-ledger swap | Both ledgers enforce compatible preimage and refund predicates | Sufficient confirmation margins, chain progress and timely observation | Hiding evidence during an unbounded partition breaks the timing argument. Verifiable timestamps cannot ensure delivery. |

For arbitrary digital title, B retains CEL as one implementation of conflict serialization. Use C for a sale whose only open choice after preparation is the payment domain's terminal outcome. A remains simpler for unencumbered transfers. D is preferable for parties already willing to hold both assets under a common ledger. It does not solve independent native custody for free. The prototype implements one B+C sale profile and a one-step onward transfer. E and D are analytical comparisons.
