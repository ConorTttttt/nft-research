use ed25519_dalek::SigningKey;
use exclusive_rights_lab::*;

fn key(i: u8) -> SigningKey {
    SigningKey::from_bytes(&[i; 32])
}
fn domain(net: u8) -> Domain {
    Domain::new([net; 32], (1..=7).map(|i| key(i).verifying_key()).collect()).unwrap()
}
fn proposal(d: &Domain, owner: u8, ids: &[u8], to: u8) -> Proposal {
    Proposal::sign(
        d,
        &key(owner),
        ids.iter()
            .map(|i| Move {
                parent: [*i; 32],
                recipient: key(to).verifying_key(),
            })
            .collect(),
    )
    .unwrap()
}
fn memory() -> Journal {
    Journal::simulation().unwrap()
}

#[test]
fn authenticated_lineage_and_replays() {
    let d = domain(1);
    let p = proposal(&d, 10, &[1], 11);
    let parents = Parents::from([([1; 32], key(10).verifying_key())]);
    let votes: Vec<_> = (0..7)
        .map(|i| {
            memory()
                .vote(&d, i, &key(i as u8 + 1), &parents, &p)
                .unwrap()
        })
        .collect();
    let children = verify(&d, &parents, &p, &votes[..5]).unwrap();
    assert_eq!(children, verify(&d, &parents, &p, &votes[2..]).unwrap());
    assert!(verify(&d, &parents, &p, &votes[..4]).is_err());
    assert!(verify(&d, &parents, &p, &vec![votes[0].clone(); 5]).is_err());
    assert!(verify(&domain(2), &parents, &p, &votes).is_err());
    assert!(verify(&d, &children, &p, &votes).is_err());
    let mut edit = p.clone();
    edit.moves[0].recipient = key(12).verifying_key();
    assert!(verify(&d, &parents, &edit, &votes).is_err());
    let moves = vec![Move {
        parent: *children.keys().next().unwrap(),
        recipient: key(12).verifying_key(),
    }];
    for (controller, valid) in [(10, false), (11, true)] {
        let next = Proposal::sign(&d, &key(controller), moves.clone()).unwrap();
        assert_eq!(
            memory().vote(&d, 0, &key(1), &children, &next).is_ok(),
            valid
        );
    }
}

#[test]
fn reopen_and_atomic_conflict() {
    let path = std::env::temp_dir().join(format!(
        "rights-{}-{}.sqlite",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ));
    let d = domain(1);
    let parents = Parents::from([
        ([1; 32], key(10).verifying_key()),
        ([2; 32], key(10).verifying_key()),
    ]);
    let first = proposal(&d, 10, &[2], 11);
    Journal::provision(&path)
        .unwrap()
        .vote(&d, 0, &key(1), &parents, &first)
        .unwrap();
    let mut journal = Journal::reopen(&path).unwrap();
    assert!(
        journal
            .vote(&d, 0, &key(1), &parents, &proposal(&d, 10, &[1, 2], 12))
            .is_err()
    );
    journal
        .vote(&d, 0, &key(1), &parents, &proposal(&d, 10, &[1], 13))
        .unwrap();
    journal.vote(&d, 0, &key(1), &parents, &first).unwrap();
    drop(journal);
    std::fs::remove_file(path).unwrap();
}

#[test]
fn generated_overlapping_request_schedules() {
    // Reproducible property test. Two faulty voters may forget every vote.
    let d = domain(1);
    let inputs: Parents = (1..=3)
        .map(|i| ([i; 32], key(10).verifying_key()))
        .collect();
    let proposals = [
        proposal(&d, 10, &[1, 2], 12),
        proposal(&d, 10, &[2, 3], 13),
        proposal(&d, 10, &[1], 14),
    ];
    for seed in 1..=48 {
        let mut journals: Vec<_> = (0..7).map(|_| memory()).collect();
        let mut schedule: Vec<_> = (0..3).flat_map(|p| (0..7).map(move |w| (p, w))).collect();
        let mut state = seed as u64;
        for i in (1..schedule.len()).rev() {
            state = state.wrapping_mul(6364136223846793005).wrapping_add(1);
            schedule.swap(i, (state >> 32) as usize % (i + 1));
        }
        let mut votes = [vec![], vec![], vec![]];
        for (p, w) in schedule {
            if w < 2 {
                journals[w] = memory();
            }
            if let Ok(v) = journals[w].vote(&d, w, &key(w as u8 + 1), &inputs, &proposals[p]) {
                votes[p].push(v);
            }
        }
        let mut used = std::collections::BTreeSet::new();
        for (p, v) in proposals.iter().zip(votes) {
            if verify(&d, &inputs, p, &v).is_ok() {
                assert!(p.moves.iter().all(|m| used.insert(m.parent)));
            }
        }
    }
}

#[test]
fn concurrent_writers_and_lost_journal() {
    let path = std::env::temp_dir().join(format!(
        "rights-race-{}-{}.sqlite",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ));
    assert!(Journal::reopen(&path).is_err());
    drop(Journal::provision(&path).unwrap());
    assert!(Journal::provision(&path).is_err());
    let barrier = std::sync::Barrier::new(2);
    let successes: usize = std::thread::scope(|scope| {
        let handles: Vec<_> = [11, 12]
            .into_iter()
            .map(|to| {
                let path = &path;
                let barrier = &barrier;
                scope.spawn(move || {
                    let mut j = Journal::reopen(path).unwrap();
                    let d = domain(1);
                    let parents = Parents::from([([1; 32], key(10).verifying_key())]);
                    let p = proposal(&d, 10, &[1], to);
                    barrier.wait();
                    j.vote(&d, 0, &key(1), &parents, &p).is_ok()
                })
            })
            .collect();
        handles
            .into_iter()
            .map(|h| usize::from(h.join().unwrap()))
            .sum()
    });
    assert_eq!(successes, 1);
    std::fs::remove_file(&path).unwrap();
    assert!(Journal::reopen(&path).is_err());
}
