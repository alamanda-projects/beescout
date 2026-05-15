#!/usr/bin/env bash
# Mac: klik dua kali file ini dari Finder.
# Wrapper untuk setup.sh agar bisa double-click di Finder.
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
bash "$DIR/setup.sh"
