use ed25519_dalek::{Signature as DalekSig, VerifyingKey};
use exclusive_rights_lab::{Domain, Id, Move, Parents, Proposal, Vote, verify};
use hdi::prelude::*;

#[derive(Debug, serde::Serialize, serde::Deserialize, SerializedBytes)]
pub struct Roots {
    pub roster: Vec<Id>,
    pub initial: Vec<(Id, Id)>,
}
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Step {
    pub moves: Vec<(Id, Id)>,
    pub owner_signature: Vec<u8>,
    pub votes: Vec<(u8, Vec<u8>)>,
}
/// Last step is the claim. Prior steps are a topological witness from DNA genesis.
#[hdk_entry_helper]
#[derive(Clone)]
pub struct History(pub Vec<Step>);
#[hdk_entry_types]
#[unit_enum(EntryTypesUnit)]
pub enum EntryTypes {
    History(History),
}

fn key(k: &Id) -> Result<VerifyingKey, String> {
    VerifyingKey::from_bytes(k).map_err(|_| "invalid public key".into())
}
fn sig(s: &[u8]) -> Result<DalekSig, String> {
    DalekSig::from_slice(s).map_err(|_| "invalid signature length".into())
}
pub fn check(network: Id, roots: Roots, h: History) -> Result<(), String> {
    if h.0.is_empty() || h.0.len() > 64 {
        return Err("history length".into());
    }
    let domain = Domain::new(
        network,
        roots.roster.iter().map(key).collect::<Result<_, _>>()?,
    )?;
    let mut parents = Parents::new();
    for (id, k) in roots.initial {
        if parents.insert(id, key(&k)?).is_some() {
            return Err("duplicate genesis".into());
        }
    }
    for step in h.0 {
        if step.moves.is_empty() || step.moves.len() > 256 || !(5..=7).contains(&step.votes.len()) {
            return Err("invalid step size".into());
        }
        let moves = step
            .moves
            .iter()
            .map(|(parent, to)| {
                Ok(Move {
                    parent: *parent,
                    recipient: key(to)?,
                })
            })
            .collect::<Result<_, String>>()?;
        let p = Proposal {
            moves,
            owner_signature: sig(&step.owner_signature)?,
        };
        let votes = step
            .votes
            .iter()
            .map(|(i, s)| {
                Ok(Vote {
                    index: usize::from(*i),
                    signature: sig(s)?,
                })
            })
            .collect::<Result<Vec<_>, String>>()?;
        let children = verify(&domain, &parents, &p, &votes)?;
        for m in p.moves {
            parents.remove(&m.parent);
        }
        parents.extend(children);
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
            let network = info
                .hash
                .get_raw_32()
                .try_into()
                .map_err(|_| wasm_error!(WasmErrorInner::Guest("DNA digest length".into())))?;
            let roots: Roots = info.modifiers.properties.try_into().map_err(|_| {
                wasm_error!(WasmErrorInner::Guest("invalid genesis properties".into()))
            })?;
            Ok(match check(network, roots, h) {
                Ok(()) => ValidateCallbackResult::Valid,
                Err(e) => ValidateCallbackResult::Invalid(e),
            })
        }
        FlatOp::CreateEntry(OpEntry::UpdateEntry { .. })
        | FlatOp::CreateRecord(OpRecord::UpdateEntry { .. }) => Ok(
            ValidateCallbackResult::Invalid("publish a new immutable claim".into()),
        ),
        _ => Ok(ValidateCallbackResult::Valid),
    }
}
