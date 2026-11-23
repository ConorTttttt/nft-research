//! Verify a portable history for one genesis entitlement. No latest-owner reads.
use ed25519_dalek::{Signature as EdSig, VerifyingKey};
use hdi::prelude::*;
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};
type Id = [u8; 32];
type Verdict<T> = Result<T, String>;
#[derive(Debug, serde::Serialize, serde::Deserialize, SerializedBytes)]
pub struct Policy {
    pub keys: Vec<Id>,
    pub users: Vec<Id>,
    pub q: u32,
    pub e: u32,
}
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub enum Step {
    Tree {
        n: u32,
        i: u32,
        to: Id,
        path: Vec<Id>,
        auth: Vec<u8>,
        votes: Vec<(usize, Vec<u8>)>,
    },
    Reset {
        reports: Vec<(usize, Option<Id>, Vec<u8>)>,
    },
}
#[hdk_entry_helper]
#[derive(Clone)]
pub struct History {
    pub genesis: u32,
    pub steps: Vec<Step>,
}
#[hdk_entry_types]
#[unit_enum(EntryTypesUnit)]
pub enum EntryTypes {
    History(History),
}
fn hash(parts: &[&[u8]]) -> Id {
    let mut h = Sha256::new();
    for p in parts {
        h.update(p);
    }
    h.finalize().into()
}
fn ensure(ok: bool, reason: &str) -> Verdict<()> {
    if ok { Ok(()) } else { Err(reason.into()) }
}
fn valid_key(id: &Id) -> Verdict<VerifyingKey> {
    let key = VerifyingKey::from_bytes(id).map_err(|_| "public key")?;
    ensure(!key.is_weak(), "weak key")?;
    Ok(key)
}
fn signature(id: &Id, sig: &[u8], parts: &[&[u8]]) -> Verdict<()> {
    valid_key(id)?
        .verify_strict(
            &parts.concat(),
            &EdSig::from_slice(sig).map_err(|_| "signature length")?,
        )
        .map_err(|_| "invalid signature".into())
}
fn check(anchor: Id, p: Policy, h: History) -> Verdict<()> {
    let n = p.keys.len();
    ensure(
        n <= 64 && n > 0 && p.q as usize <= n && p.e < p.q && 2 * (p.q as usize) > n + p.e as usize,
        "roster",
    )?;
    ensure(
        p.keys.iter().collect::<BTreeSet<_>>().len() == n && !p.users.is_empty(),
        "admission",
    )?;
    for k in p.keys.iter().chain(&p.users) {
        valid_key(k)?;
    }
    ensure(
        h.genesis < 16384 && (1..=64).contains(&h.steps.len()),
        "history bounds",
    )?;
    let domain = hash(&[
        b"phase2/domain",
        &anchor,
        &(n as u32).to_be_bytes(),
        &p.q.to_be_bytes(),
        &p.e.to_be_bytes(),
        &p.keys.concat(),
    ]);
    let mut parent = [0; 32];
    parent[28..].copy_from_slice(&h.genesis.to_be_bytes());
    let mut owner = p.users[0];
    for step in h.steps {
        let mut seen = BTreeSet::new();
        match step {
            Step::Tree {
                n: width,
                i,
                to,
                path,
                auth,
                votes,
            } => {
                ensure(
                    (1..=256).contains(&width)
                        && i < width
                        && path.len() == width.next_power_of_two().ilog2() as usize
                        && p.users.contains(&to),
                    "leaf",
                )?;
                let mut root = hash(&[b"leaf", &i.to_be_bytes(), &parent, &to]);
                for (level, sibling) in path.iter().enumerate() {
                    root = if (i >> level) & 1 == 0 {
                        hash(&[b"node", &root, sibling])
                    } else {
                        hash(&[b"node", sibling, &root])
                    };
                }
                let d = hash(&[
                    b"phase2/statement",
                    &domain,
                    b"tree",
                    &width.to_be_bytes(),
                    &root,
                ]);
                signature(&owner, &auth, &[b"owner", &d])?;
                ensure((p.q as usize..=n).contains(&votes.len()), "quorum")?;
                for (w, sig) in votes {
                    ensure(w < n && seen.insert(w), "witness index")?;
                    signature(&p.keys[w], &sig, &[b"vote", &d])?;
                }
                parent = hash(&[b"child", &d, &parent]);
                owner = to;
            }
            Step::Reset { reports } => {
                ensure(reports.len() <= n, "report count")?;
                let mut counts = BTreeMap::new();
                for (w, prior, sig) in reports {
                    ensure(w < n && seen.insert(w), "report index")?;
                    match prior {
                        Some(d) => {
                            signature(&p.keys[w], &sig, &[b"close", &domain, &parent, b"1", &d])?;
                            *counts.entry(d).or_insert(0usize) += 1;
                        }
                        None => signature(&p.keys[w], &sig, &[b"close", &domain, &parent, b"0"])?,
                    }
                }
                let negatives = seen.len() - counts.values().copied().max().unwrap_or(0);
                ensure(
                    negatives > n - p.q as usize + p.e as usize,
                    "inconclusive closure",
                )?;
                parent = hash(&[b"fixed-refund", &domain, &parent]);
            }
        }
    }
    Ok(())
}
#[hdk_extern]
pub fn validate(op: Op) -> ExternResult<ValidateCallbackResult> {
    match op.flattened::<EntryTypes, ()>()? {
        FlatOp::CreateEntry(OpEntry::CreateEntry {
            app_entry: EntryTypes::History(h),
            ..
        })
        | FlatOp::CreateRecord(OpRecord::CreateEntry {
            app_entry: EntryTypes::History(h),
            ..
        }) => {
            let info = dna_info()?;
            let anchor = info
                .hash
                .get_raw_32()
                .try_into()
                .map_err(|_| wasm_error!(WasmErrorInner::Guest("DNA hash length".into())))?;
            let policy: Policy = info
                .modifiers
                .properties
                .try_into()
                .map_err(|_| wasm_error!(WasmErrorInner::Guest("invalid properties".into())))?;
            Ok(match check(anchor, policy, h) {
                Ok(()) => ValidateCallbackResult::Valid,
                Err(e) => ValidateCallbackResult::Invalid(e),
            })
        }
        FlatOp::CreateRecord(OpRecord::UpdateEntry { .. })
        | FlatOp::CreateEntry(OpEntry::UpdateEntry { .. })
        | FlatOp::Update(OpUpdate::Entry { .. }) => {
            Ok(ValidateCallbackResult::Invalid("immutable history".into()))
        }
        _ => Ok(ValidateCallbackResult::Valid),
    }
}
