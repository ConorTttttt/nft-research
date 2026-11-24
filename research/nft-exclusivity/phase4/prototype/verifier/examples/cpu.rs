use std::{env, fs, hint::black_box};
fn micros() -> i64 {
    let mut t = libc::timespec {
        tv_sec: 0,
        tv_nsec: 0,
    };
    assert_eq!(
        unsafe { libc::clock_gettime(libc::CLOCK_PROCESS_CPUTIME_ID, &mut t) },
        0
    );
    t.tv_sec * 1_000_000 + t.tv_nsec / 1000
}
fn main() {
    let args: Vec<_> = env::args().collect();
    let p3 = fs::read(&args[1]).unwrap();
    let root3 = fs::read(&args[2]).unwrap().try_into().unwrap();
    let p4 = fs::read(&args[3]).unwrap();
    let root4 = hex::decode(fs::read_to_string(&args[4]).unwrap())
        .unwrap()
        .try_into()
        .unwrap();
    let grant = hex::decode(fs::read_to_string(&args[5]).unwrap())
        .unwrap()
        .try_into()
        .unwrap();
    for _ in 0..25 {
        let t = micros();
        for _ in 0..10 {
            black_box(phase3_verifier::verify(root3, black_box(&p3))).unwrap();
        }
        let middle = micros();
        for _ in 0..10 {
            assert_eq!(
                payment_evidence_lab::verify(root4, grant, Some(black_box(&p4))),
                payment_evidence_lab::Verdict::Paid
            );
        }
        println!("{},{}", middle - t, micros() - middle);
    }
}
