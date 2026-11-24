# Component decisions

| Adopt in the vertical slice | Evidence |
|---|---|
| Phase 2 statement/owner signature/vote verifier, persistent voter and loopback transport | Existing files imported unchanged. Phase 3 witness adds a verified child installation path. Native Rust and WASM consume the same final-envelope verifier. |
| hNFT exact-sale template, using external source pinned by SHA-256 | Real Rhai on rave_engine 0.15.0. Test source link and signer are synthetic. No hNFT payment coordinator call is trusted. |
| Exact validated-record lookup pattern | Archive coordinator uses get_details, exact action hash and Valid status. Its own integrity zome verifies every accepted envelope against DNA properties. |
| Explicit typed failure boundaries | Financial state lives in a test adapter. DHT archival accepts historical evidence. Witnesses alone decide discretionary successors. |

| Candidate | Decision and cost |
|---|---|
| dex_core | Tested native; suitable next settlement differential oracle. Its amounts are discrete u64 per unit while Unyt fuel uses string quantities. Require checked unit and precision conversion. |
| Authenticated snapshot | Adopt after defining who certifies a complete frontier and how roots advance. For 1,024 leaves, a binary SHA-256 path has 320 sibling bytes plus leaf, index, anchor and certificate. This is arithmetic, not a measured CEL history replacement. A finite path cannot recover a lost sibling. |
| FROST Ed25519 | Five individual raw signatures cost 320 bytes; one group signature costs 64, saving 256 before metadata. Both need five participants in a 5-of-7 policy. FROST requires nonce commitments and share responses, DKG, group activation, epoch rotation and a restart path for failed signers. Preprocessing can move one round offline. Independent signatures expose signer IDs for closure/accountability; retain authenticated transcripts if using FROST. |
| VRF / ZK / SSS / HPKE | Optional membership evidence, privacy, wallet recovery and protected transport respectively. No change to the lifetime equivocation bound is justified by these packages. |
| Verifiable time | Use intervals wholly before/after the contract boundary. Keep time out of hidden-payment or hidden-transfer exclusion. |
| Canonical encoding | Use versioned envelopes and pinned vectors. A replacement codec requires dual verification across a certified activation boundary. |
| hNFT, HoloHomes and inspector | Preserve discovery, metadata, booking UI and simulated execution. Show the policy domain, certificate stage and terminal evidence before displaying irrevocable status. |

The archive/engine pin HDI 0.8.1 and HDK 0.7.1 where required. DEX and HoloHomes pin 0.8.0/0.7.0; the hNFT payment test uses engine 0.13.0. Linking those full workspaces as one DNA would change dependency resolution and identity. Exchanging proof bytes and reusing only the template avoids that issue. No cross-version DNA migration was performed.
