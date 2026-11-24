//! Fixed, one-generation lab profile. Trust comes from the caller's pinned domain.
use ed25519_dalek::{Signature, VerifyingKey};
use sha2::{Digest, Sha256};
use std::collections::BTreeSet;

type Hash = [u8; 32];
const PREFIX: &[u8] = b"p3/single-unit-grant/v1";
const SCRIPT: Hash = [
    0xd8, 0x5a, 0x55, 0x9d, 0xaa, 0x87, 0x98, 0x1e, 0x6d, 0x4d, 0xfc, 0x2d, 0x03, 0x65, 0x5b, 0x0c,
    0x44, 0xcb, 0x68, 0x62, 0x4c, 0xce, 0xc8, 0x3f, 0xda, 0xe3, 0xb6, 0x77, 0x83, 0xaa, 0xc6, 0xfb,
];
fn hash(parts: &[&[u8]]) -> Hash {
    let mut h = Sha256::new();
    for part in parts {
        h.update(part);
    }
    h.finalize().into()
}
fn take<const N: usize>(input: &mut &[u8]) -> Result<[u8; N], &'static str> {
    let (head, rest) = input.split_first_chunk::<N>().ok_or("truncated")?;
    *input = rest;
    Ok(*head)
}
fn signed(key: Hash, message: &[&[u8]], input: &mut &[u8]) -> Result<(), &'static str> {
    VerifyingKey::from_bytes(&key)
        .map_err(|_| "key")?
        .verify_strict(&message.concat(), &Signature::from_bytes(&take(input)?))
        .map_err(|_| "signature")
}
pub fn verify(pin: Hash, mut proof: &[u8]) -> Result<(Hash, Hash), &'static str> {
    if proof.len() > 1536 || take::<4>(&mut proof)? != *b"P3G1" {
        return Err("format");
    }
    let [n, q, e] = take(&mut proof)?;
    if !matches!((n, q, e), (7, 5, 2) | (8, 6, 3)) {
        return Err("policy");
    }
    let network = take::<32>(&mut proof)?;
    let issuer = take(&mut proof)?;
    let users = take::<128>(&mut proof)?;
    let keys: Vec<Hash> = (0..n).map(|_| take(&mut proof)).collect::<Result<_, _>>()?;
    if keys.iter().collect::<BTreeSet<_>>().len() != usize::from(n) {
        return Err("repeated signer");
    }
    let anchor = hash(&[
        PREFIX,
        &network,
        &issuer,
        &SCRIPT,
        &10u32.to_be_bytes(),
        &16384u32.to_be_bytes(),
        &users,
    ]);
    let domain = hash(&[
        b"phase2/domain",
        &anchor,
        &u32::from(n).to_be_bytes(),
        &u32::from(q).to_be_bytes(),
        &u32::from(e).to_be_bytes(),
        &keys.concat(),
    ]);
    if domain != pin {
        return Err("trust root");
    }
    let seller: Hash = users[..32].try_into().unwrap();
    let buyer: Hash = users[32..64].try_into().unwrap();
    if users.chunks_exact(32).collect::<BTreeSet<_>>().len() != 4 {
        return Err("roles");
    }
    let parent: Hash = take(&mut proof)?;
    if parent[..30] != [0; 30] || parent[30] >= 64 {
        return Err("genesis");
    }
    let digest = hash(&[
        b"phase2/statement",
        &domain,
        b"flat",
        &1u32.to_be_bytes(),
        &hash(&[b"flat", &parent, &buyer]),
    ]);
    signed(seller, &[b"owner", &digest], &mut proof)?;
    let mut previous = None;
    for _ in 0..q {
        let [i] = take(&mut proof)?;
        if previous.is_some_and(|p| i <= p) {
            return Err("order");
        }
        signed(
            *keys.get(usize::from(i)).ok_or("witness")?,
            &[b"vote", &digest],
            &mut proof,
        )?;
        previous = Some(i);
    }
    let child = hash(&[b"child", &digest, &parent]);
    let sale = hash(&[PREFIX, b"/sale", &domain, &parent, &child]);
    let (word, controller): (&[u8], Hash) = match take(&mut proof)? {
        [0] => (b"void", seller),
        [1] => (b"paid", buyer),
        _ => return Err("outcome"),
    };
    signed(issuer, &[PREFIX, b"/terminal/", &sale, word], &mut proof)?;
    if !proof.is_empty() {
        return Err("suffix");
    }
    Ok((hash(&[PREFIX, b"/child", &sale, word]), controller))
}
