#!/bin/sh

PROGRAM="grony"
PROGRAM_LOCATION=`which $PROGRAM`
LOG_PATH="$HOME/$PROGRAM.log"
PLIST_PATH="$HOME/Library/LaunchAgents/user.$PROGRAM.plist"

xml='<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Disabled</key>
  <false/>
  <key>KeepAlive</key>
  <true/>
  <key>Label</key>
  <string>user.grony</string>
  <key>KeepAlive</key>
  <true/>
  <key>Program</key>
  <string>%s</string>
  <key>ProgramArguments</key>
  <array>
	  <string>%s</string>
      <string>start</string>
      <string>--log-level</string>
      <string>info</string>
      <string>--log-file</string>
      <string>%s</string>
  </array>
</dict>
</plist>
'

launchctl unload "$PLIST_PATH" 2> /dev/null
printf "$xml" "$PROGRAM_LOCATION" "$PROGRAM_LOCATION" "$LOG_PATH" > "$PLIST_PATH"
launchctl load "$PLIST_PATH"
