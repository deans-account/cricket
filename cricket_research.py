import argparse
from database.database import create_database

p=argparse.ArgumentParser()
sub=p.add_subparsers(dest="cmd")
i=sub.add_parser("init")
i.add_argument("database")
args=p.parse_args()
if args.cmd=="init":
    create_database(args.database)
    print(f"Created {args.database}")
else:
    p.print_help()
