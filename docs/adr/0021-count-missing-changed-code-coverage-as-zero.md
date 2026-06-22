# Count Missing Changed Code Coverage As Zero

Accepted on 2026-06-21. When a changed file is relevant source code for the configured coverage language but is missing from the Pull Request coverage report, Coverage Gate will count that file as 0% covered. Non-source files are ignored, and when no changed source files exist the changed-files coverage metric is absent rather than blocking.

**Consequences**

Coverage Gate needs language-aware source-file filtering. This prevents new or renamed source files from escaping the changed-files coverage policy simply because the coverage report omitted them.
