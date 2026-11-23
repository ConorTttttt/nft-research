# Unresolved questions

1. Can split-vote recovery preserve privately held certificates during epoch closure? Specify a reliable dissemination or finalisation barrier and prove that every certificate acceptable forever survives it. The obvious timeout variant already fails.
2. Which actual NFT terms admit permanent independent grants? Encode a lease surviving sale, a vacant-title guarantee and future delegation. Search automatically for missing read/write guards, including revocation and creation of new encumbrances.
3. Can a recipient verify only its batch leaf while preserving atomic input validation and data availability? A Merkle path authenticates inclusion. An availability certificate or retrievable parent proof is still needed. Measure bandwidth to many separate buyers.
4. Can a signer safely compact journal entries or erase retired signing keys under a realistic backup and disaster-recovery model? A local checkpoint can be rolled back with its database.
5. Which roster allocation policy balances capture risk, witness load and correlated infrastructure failures? Report per-asset and portfolio risk. Selecting a larger space of committees creates more opportunities to encounter a captured committee.
6. Can a cross-roster exchange recover after partial preparation without an always-available shared decision service? Compare a proven transaction-commit protocol to keeping coupled rights in one roster.
