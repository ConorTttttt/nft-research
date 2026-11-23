//! Compare equally authenticated transfers to distinct recipients, same five witnesses.
use ed25519_dalek::SigningKey;
use exclusive_rights_lab::*;
use std::time::Instant;
fn key(i: u8) -> SigningKey {
    SigningKey::from_bytes(&[i; 32])
}
fn main() {
    let keys: Vec<_> = (1..=7).map(key).collect();
    let d = Domain::new(
        [4; 32],
        keys.iter().map(SigningKey::verifying_key).collect(),
    )
    .unwrap();
    let owner = key(9);
    let parents: Parents = (1..=64).map(|i| ([i; 32], owner.verifying_key())).collect();
    let moves: Vec<_> = parents
        .keys()
        .enumerate()
        .map(|(i, p)| Move {
            parent: *p,
            recipient: key(i as u8 + 20).verifying_key(),
        })
        .collect();
    println!("width,median_us_for_64,min_us,max_us");
    for width in [1, 4, 16, 64] {
        let mut times = Vec::new();
        for trial in 0..12 {
            let mut nodes: Vec<_> = (0..5).map(|_| Journal::simulation().unwrap()).collect();
            let start = Instant::now();
            for group in moves.chunks(width) {
                let p = Proposal::sign(&d, &owner, group.to_vec()).unwrap();
                let votes: Vec<_> = nodes
                    .iter_mut()
                    .enumerate()
                    .map(|(i, j)| j.vote(&d, i, &keys[i], &parents, &p).unwrap())
                    .collect();
                std::hint::black_box(verify(&d, &parents, &p, &votes).unwrap());
            }
            if trial > 0 {
                times.push(start.elapsed().as_micros());
            }
        }
        times.sort();
        println!("{width},{},{},{}", times[5], times[0], times[10]);
    }
}
