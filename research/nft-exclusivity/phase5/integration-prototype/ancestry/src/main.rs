// Verify one bounded historical prefix from the parked action through DNA genesis.
use ed25519_dalek::{Signature, VerifyingKey};
use holo_hash::ActionHash;
use holochain_integrity_types::prelude::{Action, ActionData, SignedHashed};
use std::io::{self, Read};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<_> = std::env::args().skip(1).collect();
    let [tip, author, dna, accept] = args.as_slice() else {
        return Err("expected parked action, payer, DNA and funded acceptance".into());
    };
    let mut input = Vec::new();
    io::stdin().take(524289).read_to_end(&mut input)?;
    if input.len() > 524288 {
        return Err("oversized".into());
    }
    let path: Vec<SignedHashed<Action>> = serde_json::from_slice(&input)?;
    if !(2..=256).contains(&path.len()) {
        return Err("length".into());
    }
    let mut expected = Some(tip.clone());
    let mut funding = false;
    for (i, node) in path.iter().enumerate() {
        let action = &node.hashed.content;
        let h = ActionHash::with_data_sync(action);
        let id = h.to_string();
        if expected.as_ref() != Some(&id)
            || node.hashed.hash != h
            || action.author().to_string() != *author
            || action.action_seq() as usize != path.len() - 1 - i
        {
            return Err("chain mismatch".into());
        }
        let key = VerifyingKey::from_bytes(action.author().get_raw_32().try_into()?)?;
        key.verify_strict(
            &holochain_serialized_bytes::encode(action)?,
            &Signature::from_slice(node.signature.as_ref())?,
        )?;
        if i == 0 && !matches!(action.data, ActionData::CreateLink(_)) {
            return Err("wrong tip".into());
        }
        funding |= i > 0 && id == *accept && matches!(action.data, ActionData::Create(_));
        if let ActionData::Dna(d) = &action.data {
            if i + 1 != path.len() || d.dna_hash.to_string() != *dna {
                return Err("wrong DNA".into());
            }
        } else if i + 1 == path.len() {
            return Err("missing DNA".into());
        }
        expected = action.prev_action().map(|x| x.to_string());
    }
    if expected.is_some() || !funding {
        return Err("missing ancestry or funding".into());
    }
    println!(
        "Authenticated {} payer actions through DNA genesis, including funded acceptance. Pending",
        path.len()
    );
    Ok(())
}
