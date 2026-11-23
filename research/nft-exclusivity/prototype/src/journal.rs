use super::*;
use rusqlite::{Connection, TransactionBehavior, params};
pub struct Journal(Connection);
fn db(error: rusqlite::Error) -> String {
    error.to_string()
}
impl Journal {
    /// Provision an unused path; never call with a previously active signing identity.
    pub fn provision(path: &std::path::Path) -> Result<Self> {
        std::fs::OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(path)
            .map_err(|e| e.to_string())?;
        Self::initialise(
            Connection::open_with_flags(path, rusqlite::OpenFlags::SQLITE_OPEN_READ_WRITE)
                .map_err(db)?,
        )
    }
    pub fn simulation() -> Result<Self> {
        Self::initialise(Connection::open_in_memory().map_err(db)?)
    }
    fn initialise(conn: Connection) -> Result<Self> {
        conn.execute_batch(
            "PRAGMA synchronous=FULL;
            CREATE TABLE votes(domain BLOB, parent BLOB, proposal BLOB NOT NULL,
            PRIMARY KEY(domain,parent)) WITHOUT ROWID;",
        )
        .map_err(db)?;
        Ok(Self(conn))
    }
    /// Fail closed on a missing database or missing table.
    pub fn reopen(path: &std::path::Path) -> Result<Self> {
        let conn = Connection::open_with_flags(path, rusqlite::OpenFlags::SQLITE_OPEN_READ_WRITE)
            .map_err(db)?;
        conn.execute_batch(
            "PRAGMA synchronous=FULL; SELECT domain,parent,proposal FROM votes LIMIT 0;",
        )
        .map_err(db)?;
        Ok(Self(conn))
    }
    pub fn vote(
        &mut self,
        domain: &Domain,
        index: usize,
        key: &SigningKey,
        parents: &Parents,
        p: &Proposal,
    ) -> Result<Vote> {
        if domain.keys.get(index) != Some(&key.verifying_key()) {
            return Err("wrong witness".into());
        }
        let id = p.check(domain, parents)?;
        let tx = self
            .0
            .transaction_with_behavior(TransactionBehavior::Immediate)
            .map_err(db)?;
        for m in &p.moves {
            tx.execute(
                "INSERT OR IGNORE INTO votes VALUES (?1,?2,?3)",
                params![domain.tag, m.parent, id],
            )
            .map_err(db)?;
            let stored: Id = tx
                .query_row(
                    "SELECT proposal FROM votes WHERE domain=?1 AND parent=?2",
                    params![domain.tag, m.parent],
                    |r| r.get(0),
                )
                .map_err(db)?;
            if stored != id {
                return Err("input reserved for another proposal".into());
            }
        }
        tx.commit().map_err(db)?;
        Ok(Vote {
            index,
            signature: key.sign(&message(b"witness/v1", id)),
        })
    }
}
