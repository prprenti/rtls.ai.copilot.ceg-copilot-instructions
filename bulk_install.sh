#!/bin/bash

WORKAREA=$(pwd)
SCRIPT_DIR="/p/cth/pu_tu/prd/copilot_instructions/ddg/latest"

mkdir -p "$WORKAREA/.github/copilot"
cp -f "$SCRIPT_DIR"/code_review/* "$WORKAREA/.github/copilot/"
cp -f "$SCRIPT_DIR"/mcp.json "$WORKAREA/mcp.json"

git add -f .github/copilot/ mcp.json
git commit -m "Add code review instructions and updating mcp.json"
