//! The admitted source is a single test unit from a pinned genesis policy.
use ed25519_dalek::{Signature, VerifyingKey};
use sha2::{Digest, Sha256};
use std::collections::BTreeSet;
type Hash = [u8; 32];
pub const POLICY: usize = 32 * (5 + 14) + 8;
pub const TERMS: usize = 32 * 5;
pub const SIZE: usize = 4 + POLICY + TERMS + 64 + 5 * 65 + 1 + 64 + 5 * 65;
pub fn digest(domain: &[u8], fields: &[&[u8]]) -> Hash {
    let mut h = Sha256::new();
    h.update(domain);
    for f in fields {
        h.update(f)
    }
    h.finalize().into()
}
fn signature(key: &[u8], msg: &[u8], sig: &[u8]) -> bool {
    key.try_into()
        .ok()
        .and_then(|k| VerifyingKey::from_bytes(k).ok())
        .zip(Signature::from_slice(sig).ok())
        .is_some_and(|(k, s)| k.verify_strict(msg, &s).is_ok())
}
fn quorum(roster: &[u8], msg: &[u8], votes: &[u8]) -> bool {
    let mut last = None;
    votes.chunks_exact(65).all(|v| {
        let i = usize::from(v[0]);
        let ordered = last.is_none_or(|p| p < i);
        last = Some(i);
        i < 7 && ordered && signature(&roster[i * 32..i * 32 + 32], msg, &v[1..])
    })
}
#[derive(Debug, PartialEq)]
pub enum Verdict {
    Paid,
    Void,
    Pending,
    Invalid,
}
/// external grant is the ID the recipient intended, computed from the actual terms.
pub fn verify(pin: Hash, grant: Hash, body: Option<&[u8]>) -> Verdict {
    use Verdict::*;
    let Some(b) = body else { return Pending };
    if b.len() != SIZE || &b[..4] != b"P4L1" {
        return Invalid;
    }
    let p = &b[4..4 + POLICY];
    if digest(b"p4/lab-funding/v1", &[p]) != pin || p[160..168] == [0; 8] {
        return Invalid;
    }
    let keys = &p[168..];
    if keys.chunks_exact(32).collect::<BTreeSet<_>>().len() != 14 || p[96..128] == p[128..160] {
        return Invalid;
    }
    let mut at = 4 + POLICY;
    let terms = &b[at..at + TERMS];
    at += TERMS;
    if digest(b"p4/grant/v1", &[&pin, terms]) != grant {
        return Invalid;
    }
    let nft = digest(b"p4/title-reserve/v1", &[&grant]);
    if !signature(&p[128..160], &nft, &b[at..at + 64]) {
        return Invalid;
    }
    at += 64;
    if !quorum(&keys[..224], &nft, &b[at..at + 325]) {
        return Invalid;
    }
    at += 325;
    let tag = b[at];
    at += 1;
    if tag > 1 {
        return Invalid;
    }
    let terminal = digest(b"p4/disposition/v1", &[&grant, &[tag]]);
    if !signature(&p[96..128], &terminal, &b[at..at + 64]) {
        return Invalid;
    }
    at += 64;
    if !quorum(&keys[224..], &terminal, &b[at..]) {
        return Invalid;
    }
    if tag == 1 { Paid } else { Void }
}
