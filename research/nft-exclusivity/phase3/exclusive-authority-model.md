# Rights, guards and successor policies

Let an atom be (realm, asset, facet, interval cell). A marking assigns each atom one live capability with a version, controller and permitted operations. Partial-map union is defined on disjoint domains and gives a partial commutative monoid. A capability may represent many atoms as a lossless interval partition. A transition takes authenticated versions I, stable predicates R, external evidence E and emits O. Require owner authorization or a previously certified deterministic rule. Every output atom has exactly one input source, unless the pinned genesis supplies a unique mint permit. Dropping a right is affine. Duplication of an atom is forbidden. Merging two adjacent intervals requires both capabilities. Numeric capacity greater than one needs an explicit supply partition.

Two enabled deterministic operations commute if both serial orders remain enabled and give the same final marking and obligations. Disjoint writes and no read/write intersections suffice for independent execution. Conflicting absence predicates count as reads. Checking a DHT index for no leases cannot stabilize that predicate. An absence proof must cover a certified complete frontier including authority to issue new leases.

| Operation | Minimum guards within this representation | Successor |
|---|---|---|
| Sell bare title subject to leases | Current title | New title owner. Existing leases and separately assigned issuance powers retain their contractual meaning. |
| Promise vacant possession on interval J | Title plus free possession/issuance slots intersecting J | Transfer all promised facets together. An existing incompatible lease requires holder-authorized surrender or a previously agreed revocation rule. |
| Lease or book J | All affected free interval cells | One tenant capability per cell, plus disjoint residuals. Use half-open endpoints. |
| Delegate the power to issue leases | Current issuer capability in scope | New issuer or constrained grant. Retaining unrestricted issuance would duplicate the choice. |
| Revoke delegation | Shared version gate for the delegated operation and revocation | Bumps epoch and invalidates future exercise against that gate. An already certified use survives unless the original contract defined different semantics. |
| Predetermine release | Consume all guards that made recipient selection exclusive | Grant with fixed outcomes and pinned evidence policy. Repeated exercise derives identical children. |
| Move a committee | Old parent certificate binds successor policy and child ID | New roster decides only descendants. Unresolved parents still need the old policy. |
| Batch or cross-domain settlement | Union of guards, full statement, validated dependencies | Same statement across all participating authorities, or monotone fixed exercises where choices already moved upstream. |

A land title may include issuance of future leases in its definition. Then a purported bare-title sale must also move that power. Physical key revocation, eviction and control of copied media fall outside this algebra. Time evidence proving an interval has ended can enable a prearranged reversion. A challenge with uncertainty spanning the endpoint stays pending. Irrevocable offline leases and immediate unobservable revocation cannot both be promised.

## Deriving guards

For a finite Cartesian state space and a deterministic partial function expressed as refusal or sparse writes, coordinate i belongs to the least semantic input support iff changing only i changes that result for some assignment. Necessity follows from the two assignments. Sufficiency follows by changing non-support coordinates one at a time. Compute the union of potential writes separately. A verifier can reproduce the table and certificate of sensitivity before admitting a rule. A live transition still has to fence each changing predicate it relies on. Read-only sharing requires a stable version protocol or an immutable commitment.

The executable compiler checks all projections independently on three binary facets. The diamond checker separately tests title, vacant sale, lease, delegation and revocation with four controller labels. The result is exact for this coordinate vocabulary and full product domain. Correlated states may admit interchangeable guard sets and lack a unique least support. Dynamic key selection, unbounded state and arbitrary Rhai invalidate the finite decision procedure. Pin a small declarative language or use a conservative whole-resource guard. Local typing alone has no authority over a remote copy.
