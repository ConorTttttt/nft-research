//! Fixed-roster research core. The caller provisions authenticated genesis and verified parents.
use ed25519_dalek::{Signature, Signer, SigningKey, VerifyingKey};
#[cfg(feature = "journal")]
mod journal;
#[cfg(feature = "journal")]
pub use journal::Journal;
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};

pub type Id = [u8; 32];
pub type Parents = BTreeMap<Id, VerifyingKey>;
pub type Result<T> = std::result::Result<T, String>;

/// External trust anchor. Order defines witness indices. Exactly seven keys, five votes.
pub struct Domain {
    tag: Id,
    keys: Vec<VerifyingKey>,
}
impl Domain {
    pub fn new(network_and_genesis: Id, keys: Vec<VerifyingKey>) -> Result<Self> {
        let distinct: BTreeSet<_> = keys.iter().map(VerifyingKey::to_bytes).collect();
        if keys.len() != 7 || distinct.len() != 7 || keys.iter().any(VerifyingKey::is_weak) {
            return Err("invalid roster".into());
        }
        let mut hash = Sha256::new();
        hash.update(b"exclusive-rights/domain/v1");
        hash.update(network_and_genesis);
        for key in &keys {
            hash.update(key.as_bytes());
        }
        Ok(Self {
            tag: hash.finalize().into(),
            keys,
        })
    }
}

#[derive(Clone)]
pub struct Move {
    pub parent: Id,
    pub recipient: VerifyingKey,
}
#[derive(Clone)]
pub struct Proposal {
    pub moves: Vec<Move>,
    pub owner_signature: Signature,
}
fn digest(domain: &Domain, moves: &[Move]) -> Result<Id> {
    if moves.is_empty()
        || moves.len() > 256
        || moves.windows(2).any(|w| w[0].parent >= w[1].parent)
        || moves.iter().any(|m| m.recipient.is_weak())
    {
        return Err("invalid or noncanonical move list".into());
    }
    let mut hash = Sha256::new();
    hash.update(b"exclusive-rights/proposal/v1");
    hash.update(domain.tag);
    hash.update((moves.len() as u32).to_be_bytes());
    for m in moves {
        hash.update(m.parent);
        hash.update(m.recipient.as_bytes());
    }
    Ok(hash.finalize().into())
}
fn message(role: &[u8], id: Id) -> Vec<u8> {
    [role, &id].concat()
}
impl Proposal {
    pub fn sign(domain: &Domain, owner: &SigningKey, moves: Vec<Move>) -> Result<Self> {
        let id = digest(domain, &moves)?;
        Ok(Self {
            moves,
            owner_signature: owner.sign(&message(b"owner/v1", id)),
        })
    }
    fn check(&self, domain: &Domain, parents: &Parents) -> Result<Id> {
        let id = digest(domain, &self.moves)?;
        let owner = parents.get(&self.moves[0].parent).ok_or("unknown parent")?;
        if owner.is_weak()
            || self
                .moves
                .iter()
                .any(|m| parents.get(&m.parent) != Some(owner))
        {
            return Err("unverified parent or different controllers".into());
        }
        owner
            .verify_strict(&message(b"owner/v1", id), &self.owner_signature)
            .map_err(|_| "invalid owner signature")?;
        Ok(id)
    }
}
#[derive(Clone)]
pub struct Vote {
    pub index: usize,
    pub signature: Signature,
}
/// Output coordinates derive only from the statement. Different signer subsets yield identical children.
pub fn verify(domain: &Domain, parents: &Parents, p: &Proposal, votes: &[Vote]) -> Result<Parents> {
    let id = p.check(domain, parents)?;
    if !(5..=7).contains(&votes.len()) {
        return Err("certificate size".into());
    }
    let mut seen = BTreeSet::new();
    for vote in votes {
        if !seen.insert(vote.index) {
            return Err("duplicate vote".into());
        }
        domain
            .keys
            .get(vote.index)
            .ok_or("unknown witness")?
            .verify_strict(&message(b"witness/v1", id), &vote.signature)
            .map_err(|_| "invalid witness signature")?;
    }
    Ok(p.moves
        .iter()
        .map(|m| {
            let mut hash = Sha256::new();
            hash.update(b"exclusive-rights/child/v1");
            hash.update(id);
            hash.update(m.parent);
            (hash.finalize().into(), m.recipient)
        })
        .collect())
}
