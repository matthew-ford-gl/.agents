#!/usr/bin/env python3
import argparse
import datetime
import json
import pathlib


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("phase")
    parser.add_argument("--tool-calls", type=int, default=0)
    parser.add_argument("--remote-calls", type=int, default=0)
    parser.add_argument("--input-bytes", type=int, default=0)
    parser.add_argument("--output-bytes", type=int, default=0)
    parser.add_argument("--retries", type=int, default=0)
    parser.add_argument("--reason", default="")
    parser.add_argument("--outcome", default="")
    args = parser.parse_args()
    event = vars(args)
    path = pathlib.Path(event.pop("path"))
    event["timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as target:
        target.write(json.dumps(event, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
