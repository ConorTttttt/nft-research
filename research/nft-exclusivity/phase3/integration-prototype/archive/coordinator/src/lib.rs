use grant_integrity::{EntryTypes, Evidence};
use hdk::prelude::*;
#[hdk_extern]
pub fn publish(input: Vec<u8>) -> ExternResult<ActionHash> {
    create_entry(EntryTypes::Evidence(Evidence(input)))
}
#[hdk_extern]
pub fn retrieve(hash: ActionHash) -> ExternResult<Option<Vec<u8>>> {
    match get_details(hash.clone(), GetOptions::network())? {
        Some(Details::Record(d)) if d.record.action_address() == &hash => match d.validation_status
        {
            ValidationStatus::Valid => Ok(d
                .record
                .entry()
                .to_app_option::<Evidence>()
                .map_err(|e| wasm_error!(WasmErrorInner::Guest(format!("{e:?}"))))?
                .map(|e| e.0)),
            ValidationStatus::Abandoned => Ok(None),
            ValidationStatus::Rejected => {
                Err(wasm_error!(WasmErrorInner::Guest("rejected record".into())))
            }
        },
        None => Ok(None),
        _ => Err(wasm_error!(WasmErrorInner::Guest(
            "unexpected record details".into()
        ))),
    }
}
