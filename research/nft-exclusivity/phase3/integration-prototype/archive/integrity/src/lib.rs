use hdi::prelude::*;
#[derive(Debug, serde::Serialize, serde::Deserialize, SerializedBytes)]
pub struct Policy {
    pub domain: [u8; 32],
}
#[hdk_entry_helper]
#[derive(Clone)]
pub struct Evidence(pub Vec<u8>);
#[hdk_entry_types]
#[unit_enum(UnitEntryTypes)]
pub enum EntryTypes {
    Evidence(Evidence),
}
#[hdk_extern]
pub fn validate(op: Op) -> ExternResult<ValidateCallbackResult> {
    use ValidateCallbackResult::{Invalid, Valid};
    Ok(match op.flattened::<EntryTypes, ()>()? {
        FlatOp::CreateEntry(OpEntry::CreateEntry {
            app_entry: EntryTypes::Evidence(proof),
            ..
        })
        | FlatOp::CreateRecord(OpRecord::CreateEntry {
            app_entry: EntryTypes::Evidence(proof),
            ..
        }) => {
            let pin: Policy = dna_info()?
                .modifiers
                .properties
                .try_into()
                .map_err(|_| wasm_error!(WasmErrorInner::Guest("policy pin".into())))?;
            match phase3_verifier::verify(pin.domain, &proof.0) {
                Ok(_) => Valid,
                Err(reason) => Invalid(reason.into()),
            }
        }
        FlatOp::CreateEntry(OpEntry::UpdateEntry { .. })
        | FlatOp::CreateRecord(OpRecord::UpdateEntry { .. })
        | FlatOp::Update(_) => Invalid("immutable evidence".into()),
        _ => Valid,
    })
}
