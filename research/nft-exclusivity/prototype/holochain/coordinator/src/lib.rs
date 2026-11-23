use hdk::prelude::*;
use rights_integrity::{EntryTypes, History};
#[hdk_extern]
pub fn publish(history: History) -> ExternResult<ActionHash> {
    create_entry(EntryTypes::History(history))
}
