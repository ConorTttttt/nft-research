use std::{env, fs};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<_> = env::args().skip(1).collect();
    let [pin, blob] = args.as_slice() else {
        return Err("expected binary trust root and proof files".into());
    };
    let pin: [u8; 32] = fs::read(pin)?.try_into().map_err(|_| "pin width")?;
    let bytes = fs::read(blob)?;
    let (child, controller) = phase3_verifier::verify(pin, &bytes)?;
    for value in [child, controller] {
        for b in value {
            print!("{b:02x}");
        }
        println!();
    }
    Ok(())
}
