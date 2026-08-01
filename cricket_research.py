import argparse
from importer.archive_reader import scan_archive
from database.database import Database

parser=argparse.ArgumentParser()
sub=parser.add_subparsers(dest="cmd")
p1=sub.add_parser("init"); p1.add_argument("db")
p2=sub.add_parser("scan"); p2.add_argument("archive")
args=parser.parse_args()

if args.cmd=="init":
    Database(args.db).initialise()
    print("Database initialised")
elif args.cmd=="scan":
    stats=scan_archive(args.archive)
    print(f"Archive: {stats['archive']}")
    print(f"Members: {stats['members']}")
    print(f"BZ2 files: {stats['bz2_files']}")
    print(f"Size (bytes): {stats['size_bytes']}")
else:
    parser.print_help()
