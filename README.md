# Betfair Research Lab v0.4

Version 0.4 adds a working Betfair historical stream parser.

## Features

- Scan Betfair `.tar` archives
- Open nested `.bz2` market files directly from the archive
- Parse line-delimited Betfair Stream API JSON
- Extract market definitions, runners, event names, market type and timestamps
- Produce a metadata audit in JSON or CSV
- Skip malformed files without stopping the whole audit
- Database initialisation remains available

## Commands

Initialise a database:

```bash
python cricket_research.py init cricket_research.sqlite
```

Scan an archive:

```bash
python cricket_research.py scan data.tar
```

Audit Betfair market metadata:

```bash
python cricket_research.py audit data.tar --output audit.csv
```

Limit the audit while testing:

```bash
python cricket_research.py audit data.tar --limit 100
```

The next version will add Test Match filtering and database ingestion.
