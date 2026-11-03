"""Command-line interface.

Usage (from the project directory):
  python -m nearguard.cli check <account_id> [--network mainnet|testnet]
                                             [--agent <agent_id>]
  python -m nearguard.cli report <account_id> --reason "..." \
          --evidence "..." --by <reporter_id>

`check` prints the verdict as JSON on stdout.
"""

import argparse
import json
import sys

from . import service, store

DEFAULT_AGENT = "demo-agent.near"


def main(argv=None):
    parser = argparse.ArgumentParser(prog="nearguard")
    sub = parser.add_subparsers(dest="command", required=True)

    p_check = sub.add_parser("check", help="check a receiver account")
    p_check.add_argument("account_id")
    p_check.add_argument("--network", default="mainnet",
                         choices=["mainnet", "testnet"])
    p_check.add_argument("--agent", default=DEFAULT_AGENT)

    p_report = sub.add_parser("report", help="add an account to the blocklist")
    p_report.add_argument("account_id")
    p_report.add_argument("--reason", required=True)
    p_report.add_argument("--evidence", required=True,
                          help="required: link or note backing the report")
    p_report.add_argument("--by", required=True, dest="reported_by")

    args = parser.parse_args(argv)

    if args.command == "check":
        result = service.check(args.agent, args.account_id, args.network)
        print(json.dumps(result, indent=2))
        return 0
    if args.command == "report":
        entry = store.report_to_blocklist(
            args.account_id, args.reason, args.evidence, args.reported_by)
        print(json.dumps({args.account_id: entry}, indent=2))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
