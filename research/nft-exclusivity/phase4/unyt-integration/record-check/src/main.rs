//! Verify one historical Holochain Create or CreateLink. No statement about competing histories.
use ed25519_dalek::{Signature, VerifyingKey};
use holo_hash::{ActionHash, EntryHash};
use holochain_integrity_types::prelude::{ActionData, Entry, Record};
use std::io::{self, Read};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<_> = std::env::args().skip(1).collect();
    let [expected_action, expected_author] = args.as_slice() else {
        return Err("expected action ID and author required".into());
    };
    let mut input = Vec::new();
    io::stdin().take(1048577).read_to_end(&mut input)?;
    if input.len() > 1048576 {
        return Err("oversize record".into());
    }
    let record: Record = serde_json::from_slice(&input)?;
    let hash = ActionHash::with_data_sync(record.action());
    let action = record.action();
    if hash != *record.action_address()
        || hash.to_string() != *expected_action
        || action.author().to_string() != *expected_author
    {
        return Err("action/author mismatch".into());
    }
    let key = VerifyingKey::from_bytes(action.author().get_raw_32().try_into()?)?;
    let encoded = holochain_serialized_bytes::encode(action)?;
    key.verify_strict(
        &encoded,
        &Signature::from_slice(record.signature().as_ref())?,
    )?;
    if let ActionData::CreateLink(link) = &action.data {
        println!("{}", hex::encode(link.tag.as_ref()));
        return Ok(());
    }
    if !matches!(action.data, ActionData::Create(_)) {
        return Err("expected Create".into());
    }
    let entry = record.entry().as_option().ok_or("missing entry")?;
    if Some(&EntryHash::with_data_sync(entry)) != action.entry_hash() {
        return Err("entry hash mismatch".into());
    }
    let Entry::App(bytes) = entry else {
        return Err("expected app entry".into());
    };
    println!("{}", hex::encode(bytes.bytes()));
    Ok(())
}
