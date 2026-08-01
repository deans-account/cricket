# Import Validation

Before declaring the importer production ready, each archive import should verify:

- Archive SHA256
- Duplicate archive detection
- Duplicate market IDs
- Runner count
- Settlement presence
- Price history exists
- SQLite integrity
- Import statistics

Expected workflow:

1. init database
2. import archive
3. verify database
4. optimise strategies
