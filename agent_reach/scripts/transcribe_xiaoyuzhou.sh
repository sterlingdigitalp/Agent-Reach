#!/usr/bin/env bash
# Compatibility launcher for Xiaoyuzhou transcription.
#
# The Python pipeline owns downloads, bounded subprocesses, API requests, and
# temporary-file cleanup. Keeping credentials out of curl argv avoids exposure
# in process listings.

set -euo pipefail

usage() {
    echo "Usage: transcribe.sh <xiaoyuzhoufm.com URL> [output file]" >&2
}

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
    usage
    exit 2
fi

source_url=$1

case "$source_url" in
    https://xiaoyuzhoufm.com/*|https://*.xiaoyuzhoufm.com/*)
        ;;
    *)
        echo "Refusing non-Xiaoyuzhou URL: $source_url" >&2
        exit 2
        ;;
esac

echo "Privacy notice: audio will be uploaded to the configured Groq/OpenAI provider." >&2
if [ "$#" -eq 2 ]; then
    exec python3 -m agent_reach.cli transcribe "$source_url" --output "$2"
fi
exec python3 -m agent_reach.cli transcribe "$source_url"
