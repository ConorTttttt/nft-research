# Two tight bounds for direct witness certificates

Fix one input, n admitted identities and a q-signature transfer rule. A correct identity reserves at most one proposal digest per input and cannot retract a signature. Let e bound the number of distinct identities that can depart from this rule, forget a prior vote, invent a closure report or sign against a fence over the full validity horizon of this input. A restored key and a clone count as one faulty *identity*. Let s be the maximum number that may withhold during an otherwise uncontended request. The sets for safety and liveness may overlap. Require authenticated owner, roster, domain, canonical messages and an injective transition representation up to hash collision.

## 1. Buying a rollback budget

Two final sets overlap in at least 2q−n identities. They exclude a conflict iff 2q−n>e in the uniform, one-round, arbitrary-subset model. Progress with s silent requires q≤n−s. Thus n≥e+2s+1. At equality q=e+s+1. Necessity follows by constructing minimum-intersection quorums and allowing all intersection identities to equivocate. Sufficiency follows from one never-equivocating identity shared by every two conflicting quorums.

For two Byzantine operators **plus** one other lifetime rollback, e=3. With at most two silent, n=8,q=6 is minimal. If the recovering witness must also be offline alongside two silent Byzantine witnesses, s=3 and the minimum becomes n=10,q=7. Seven of nine would also be safe with e=3 but stalls with three silent; six of nine is unsafe. A bound on simultaneously broken machines alone gives no such guarantee against accumulating old signatures.

## 2. When exactly is it safe to refund an input?

Define one predetermined administrative outcome R(s) returning its rights and controller unchanged at a fresh version H(prefix,domain,s). An honest witness signs a closure report only after irrevocably stopping new votes for s. Its report names its one previously reserved digest or empty. A reservation whose vote was never released is conservatively counted as a possible signature. Reissuing the identical prior vote remains safe. The owner may request closure; the refund semantics are part of the original policy. Closing is a potentially irreversible abandon attempt.

Collect k authenticated reports from distinct identities for precisely this domain and parent. For any transfer digest x, let a(x) be the number of these reports naming x. An unmentioned digest has count zero. A correct reporter naming another value or empty cannot have signed x and cannot sign it later. The maximum possible number of x votes, including hidden and future signatures, is

    U(x) = min(n, n − k + a(x) + e).

The three contributions are absent reporters, matching reporters, and up to e untruthful negative reporters. The cap prevents counting an identity twice. The bound is tight *from these reports alone*: choose up to e negative reporters as faulty, let them sign x, and let missing and matching identities sign x. Other policy information can exclude particular digests; tightness presumes that the digest's proposal is independently admissible. This is a per-candidate epistemic bound, and different maxima can require different fault assignments.

Consequently every possible transfer is excluded exactly when

    k − max_x a(x) ≥ n − q + e + 1.

The maximum defaults to zero for all-empty reports. Verification needs a histogram of reported digests, not enumeration of future proposals. Each candidate has a blocking set of permanent negative reports; the blocking set may differ by candidate. For 7/5/2 the threshold is five negatives; for 8/6/3 it is six. A report set can contain a genuine minority reservation and still prove safe closure. For example two A, two B, one C and two empty suffice at 7/5/2. Five empty reports also suffice. Four never suffice there, even for zero visible votes.

**Composition proof.** Two transfers conflict by theorem 1. A valid reset excludes *every* q-vote transfer for that parent by theorem 2, including certificates assembled later from old signatures. Two valid reset proofs produce exactly the same child, regardless of signers, order or report contents. Bind owner, rights and admissible policy to the authenticated predecessor. Induction on ancestry then gives authorised exclusive succession across any number of moves and resets. For an atomic batch, exclusion of even one parent rules out that whole statement. A reset on one parent does not release others. Hashing the reset proof itself into the child ID would break the induction.

**Liveness.** An uncontended correct client with verified parents and q responsive willing signers eventually completes under eventual delivery, finite processing and stable storage. Reset completes when sufficient permanent reports meet the displayed inequality, the recovery client can obtain them, and the child can reach its next quorum. Neither property ensures progress for every adversarial split. There is no probabilistic liveness or time bound in the asynchronous model. These deductions specialise quorum intersection and blocking sets. No priority or cryptographic novelty claim is made. [Byzantine quorum systems](https://doi.org/10.1007/s004460050050)

## Nonuniform trust

For each digest x let N(x) be the set of reporters that permanently exclude x. For an admissible family of final quorums Q and possible faulty sets F, the exact blocking condition is: for every Q and F, (Q ∩ N(x)) minus F is nonempty. Apply it to all reported candidates and one representative unmentioned digest. If it fails for a feasible x, all negative reporters in one possible final quorum can be faulty in the same admissible execution. This recovers the counting bound for uniform thresholds. It can also express correlated-operator assumptions such as “no two regions share an administrator”, if those assumptions can actually be justified. It gives an algorithm for checking a finite policy; it does not establish that a proposed membership policy matches real operators.

## Why the rule permits one fixed refund, never “finalise the last plausible candidate”

This tempting stronger repair rule forks even with **seven honest processes**. Assume verifiers must tolerate e=2, q=5. The actual seven permanent reports are A,A,B,B,empty,empty,empty. A collector omitting one B sees six reports. Only A could still reach five under its fault model. A collector omitting one A obtains the symmetric conclusion for B. Neither candidate actually has five signatures. If each six-report proof could *promote* its sole possible candidate, two incompatible successors would become final. With all seven reports, both old candidates are impossible and the single fixed refund is safe. This illustrates the difference between an upper bound on a *hidden original certificate* and authorisation to create a *new kind of positive decision*. Adding that decision requires an intersection/locking argument across the repair paths themselves. [Executable counterexample](formal-models/ambiguous_repair.py)
