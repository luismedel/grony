#!/bin/sh

PROGRAM="grony"
PLIST_PATH="$HOME/Library/LaunchAgents/user.$PROGRAM.plist"

launchctl unload "$PLIST_PATH" 2> /dev/null
rm "$PLIST_PATH" 2> /dev/null
