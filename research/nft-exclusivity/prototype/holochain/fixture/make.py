"""Prepare disposable, public test keys, bundle manifests or one signed test payload."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
from shutil import copyfile
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

def key(n):
    return Ed25519PrivateKey.from_private_bytes(bytes([n]) * 32)

def public(n):
    return key(n).public_key().public_bytes_raw()

def digest(*parts):
    return hashlib.sha256(b''.join(parts)).digest()

def manifests(out):
    dna = out / 'dna'
    dna.mkdir(parents=True, exist_ok=True)
    for zome in ['rights_integrity','rights_coordinator']:
        source = Path(__file__).resolve().parents[1] / 'target/wasm32-unknown-unknown/release' / (zome + '.wasm')
        copyfile(source, dna / source.name)
    properties = {'roster':[list(public(i)) for i in range(1,8)],
                  'initial':[[[1]*32,list(public(9))]]}
    manifest = {'manifest_version':'0','name':'rights_lab','integrity':{
        'network_seed':'local-fixture','properties':properties,
        'zomes':[{'name':'rights_integrity','path':'rights_integrity.wasm'}]},
        'coordinator':{'zomes':[{'name':'rights_coordinator','path':'rights_coordinator.wasm',
        'dependencies':[{'name':'rights_integrity'}]}]}}
    (dna/'dna.yaml').write_text(json.dumps(manifest))
    app = {'manifest_version':'0','name':'rights_lab','roles':[{'name':'rights',
           'provisioning':{'strategy':'create','deferred':False},
           'dna':{'path':'dna/rights_lab.dna','clone_limit':0}}]}
    (out/'happ.yaml').write_text(json.dumps(app))

def payload(dna_hash):
    raw = base64.urlsafe_b64decode(dna_hash[1:]+'===')
    assert len(raw)==39
    domain = digest(b'exclusive-rights/domain/v1',raw[3:35],*(public(i) for i in range(1,8)))
    parent = bytes([1])*32
    statement = digest(b'exclusive-rights/proposal/v1',domain,(1).to_bytes(4,'big'),parent,public(10))
    return [{'moves':[[list(parent),list(public(10))]],
             'owner_signature':list(key(9).sign(b'owner/v1'+statement)),
             'votes':[[i,list(key(i+1).sign(b'witness/v1'+statement))] for i in range(5)]}]

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--out',type=Path)
    group.add_argument('--dna-hash')
    args=parser.parse_args()
    if args.out: manifests(args.out)
    else: print(json.dumps(payload(args.dna_hash)))
