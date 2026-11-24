use payment_evidence_lab::{SIZE, Verdict, verify};
use std::{env, fs, io::Read};
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<_> = env::args().skip(1).collect();
    let [mode, pin, grant, path] = args.as_slice() else {
        return Err("mode pin grant file".into());
    };
    let parse = |s: &str| -> Result<[u8; 32], Box<dyn std::error::Error>> {
        Ok(hex::decode(s)?.try_into().map_err(|_| "pin length")?)
    };
    let root = parse(pin)?;
    let expected = parse(grant)?;
    let body = match fs::File::open(path) {
        Ok(file) => {
            let mut v = Vec::new();
            file.take((SIZE + 1) as u64).read_to_end(&mut v)?;
            Some(v)
        }
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => None,
        Err(e) => return Err(e.into()),
    };
    let verdict = match mode.as_str() {
        "lab" => verify(root, expected, body.as_deref()),
        // No Unyt exclusion policy authenticated. Recognizable lab envelopes cannot cross realms.
        "unyt" => {
            if body.as_ref().is_some_and(|b| b.starts_with(b"P4L1")) {
                Verdict::Invalid
            } else {
                Verdict::Pending
            }
        }
        _ => return Err("unsupported verifier mode".into()),
    };
    println!("{verdict:?}");
    Ok(())
}
