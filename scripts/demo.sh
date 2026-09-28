#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH=src
echo "======== 今年黄金会员的成交额 ========"
python3 -m joinpath.cli --schema examples/schema.json "今年黄金会员的成交额"
echo
echo "======== 每个品类的销量 ========"
python3 -m joinpath.cli --schema examples/schema.json "每个品类的销量"
echo
echo "======== gold member GMV this year ========"
python3 -m joinpath.cli --schema examples/schema.json "gold member GMV this year"
