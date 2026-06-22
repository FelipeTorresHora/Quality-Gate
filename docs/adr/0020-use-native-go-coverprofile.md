# Use Native Go Coverprofile

Accepted on 2026-06-21. Go Coverage Gate support will initially use the native `go test ./... -coverprofile=coverage.out` output instead of requiring a conversion tool such as Cobertura XML. This keeps the MVP dependency surface smaller while still allowing per-file coverage to be calculated from the Go cover profile.

**Consequences**

The Coverage Gate needs a parser for Go coverprofile output. Go coverage defaults should not require external coverage conversion binaries.
