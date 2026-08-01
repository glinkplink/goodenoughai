"""Command-line interface for the approved architecture."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from . import __version__
from .exceptions import MigrationError
from .reproduction import verify_batch_reproduction
from .repository import SQLiteRepository


PLACEHOLDER_EXIT = 69


def _placeholder(command: str) -> int:
    print(
        f"goodenough-bench {command}: placeholder only; behavior is not implemented",
        file=sys.stderr,
    )
    return PLACEHOLDER_EXIT


def _add_placeholder(parent: argparse._SubParsersAction[argparse.ArgumentParser], name: str) -> None:
    parser = parent.add_parser(name, help=f"placeholder: {name} is not implemented")
    parser.set_defaults(handler=lambda _args, command=name: _placeholder(command))


def _cmd_batch_reproduce(args: argparse.Namespace) -> int:
    database = Path(args.database)
    if not database.is_file():
        print(
            f"goodenough-bench batch reproduce: operational database does not exist: {database}",
            file=sys.stderr,
        )
        return 2
    try:
        repository = SQLiteRepository.open_for_verification(database)
    except MigrationError as error:
        print(
            f"goodenough-bench batch reproduce: database schema is unsupported: {error}",
            file=sys.stderr,
        )
        return 2
    try:
        report = verify_batch_reproduction(repository, args.batch)
    finally:
        repository.close()

    print(json.dumps(report.model_dump(mode="json"), sort_keys=True, indent=2))
    if not args.verify_checksum:
        return 0
    return 0 if report.verified else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="goodenough-bench",
        description="GoodEnough.ai local benchmark CLI (command scaffolding only).",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", metavar="COMMAND")

    cases = commands.add_parser("cases", help="case operations (placeholders)")
    case_commands = cases.add_subparsers(dest="cases_command", metavar="COMMAND")
    _add_placeholder(case_commands, "validate")

    models = commands.add_parser("models", help="model operations (placeholders)")
    model_commands = models.add_subparsers(dest="models_command", metavar="COMMAND")
    _add_placeholder(model_commands, "probe")

    batch = commands.add_parser("batch", help="batch operations")
    batch_commands = batch.add_subparsers(dest="batch_command", metavar="COMMAND")
    for name in ("run", "score", "export"):
        _add_placeholder(batch_commands, name)

    reproduce = batch_commands.add_parser(
        "reproduce",
        help="verify frozen batch reproduction metadata checksum",
    )
    reproduce.add_argument(
        "--database",
        required=True,
        help="path to the operational SQLite database",
    )
    reproduce.add_argument(
        "--batch",
        required=True,
        help="batch_id to verify",
    )
    reproduce.add_argument(
        "--verify-checksum",
        action="store_true",
        help="recompute and compare the stored reproduction_checksum",
    )
    reproduce.set_defaults(handler=_cmd_batch_reproduce)

    _add_placeholder(commands, "import")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 0
    return int(handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
