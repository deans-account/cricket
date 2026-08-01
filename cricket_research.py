import argparse
from database.database import Database

parser=argparse.ArgumentParser(description="Betfair Cricket Research")
sub=parser.add_subparsers(dest="cmd")
p=sub.add_parser("init")
p.add_argument("db")
args=parser.parse_args()

if args.cmd=="init":
    db=Database(args.db)
    db.initialise()
    print(f"Database initialised: {args.db}")
else:
    parser.print_help()
