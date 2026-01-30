#!/bin/bash
# Edit/Write前に最新をプル

git pull --rebase origin HEAD 2>/dev/null || true
