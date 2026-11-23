# Exclusive NFT transfers on Holochain

**Finding.** Choosing between two spend destinations requires a common non-equivocating decision at the point where the choices diverge. The unit requiring that decision can be smaller than an NFT. If the destination was fixed irrevocably in advance, presenting the resulting entitlement can require zero new witness messages.

The implementation uses immutable, independently assignable rights and an optional atomic batch within one witness domain. Use a single title right for an ordinary NFT. A split is meaningful only when the legal and application semantics survive a title change. The main measurable gain over one certificate per transition is amortisation. Neither batching nor certified versioned objects is claimed as a new cryptographic primitive.

| Read | Question |
|---|---|
| [Problem](problem-definition.md) and [first principles](first-principles-analysis.md) | What can a disconnected recipient know? |
| [Candidates](candidate-architectures.md) and [mathematics](mathematical-results.md) | Which costs are necessary and which depend on the design? |
| [Architecture](selected-architecture.md) and [assumptions](security-assumptions.md) | What does a recipient actually verify? |
| [Models](formal-models/) and [results](formal-verification-results.md) | Which interleavings and failures were explored? |
| [Rust and Holochain code](prototype/) and [adversarial tests](adversarial-tests.md) | What executes today? |
| [Comparison](architecture-comparison.md) and [measurements](performance-results.md) | When does this beat the baseline? |
| [Open questions](open-research-questions.md) and [roadmap](implementation-roadmap.md) | What still separates this from a deployable system? |
