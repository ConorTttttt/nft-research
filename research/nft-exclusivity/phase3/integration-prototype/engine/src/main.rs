// Execute the pinned public hNFT exact-sale template on synthetic parked input.
use hdi::prelude::{ActionHash, ActionHashB64, AgentPubKey, AgentPubKeyB64};
use rave_engine::prelude::RhaiEngine;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<_> = std::env::args().skip(1).collect();
    let [script, seller, asset, source, price, paid] = args.as_slice() else {
        return Err("expected script, seller, asset, source, price, paid".into());
    };
    let code = std::fs::read_to_string(script)?;
    if hex::encode(Sha256::digest(code.as_bytes()))
        != "d85a559daa87981e6d4dfc2d03655b0c44cb68624ccec83fdae3b67783aac6fb"
    {
        return Err("unexpected template".into());
    }
    let key: [u8; 32] = hex::decode(seller)?
        .try_into()
        .map_err(|_| "seller length")?;
    let id: [u8; 32] = hex::decode(source)?
        .try_into()
        .map_err(|_| "source length")?;
    let receiver = AgentPubKeyB64::from(AgentPubKey::from_raw_32(key.to_vec())).to_string();
    let link = ActionHashB64::from(ActionHash::from_raw_32(id.to_vec())).to_string();
    let input = json!({"inputs":{"seller":{"data":receiver},"price":{"data":{"0":price}},"nft_id":{"data":asset}},
        "consumed_inputs":{"buyer_spends":[{"data":{"amount":{"0":paid},"source":link}}]}});
    let run = RhaiEngine::new()
        .execute(&input, rmp_serde::to_vec(&code)?, None)
        .map_err(|e| format!("{e:?}"))?;
    let output: Value = serde_json::to_value(run.output)?;
    let expected = json!([{"receiver": receiver, "amounts":{"0":price},"sources":[link]}]);
    if output["unyt_allocation"] != expected || output["computed_values"]["nft_id"] != *asset {
        return Err(format!("unexpected output {output}").into());
    }
    println!("{}", output);
    Ok(())
}
