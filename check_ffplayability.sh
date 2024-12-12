#!/bin/bash

# Define the folder to process
FOLDER="/run/media/bec/LaCie/Aviary-Data"

# Check if the folder exists
if [ ! -d "$FOLDER" ]; then
    echo "Folder '$FOLDER' does not exist. Please provide a valid folder path."
    exit 1
fi

# Loop through each file in the folder
for FILE in "$FOLDER"/*; do
    # Check if it's a regular file
    if [ -f "$FILE" ]; then
        echo "Processing file: $FILE"

        # Start ffplay in the background with timeout and capture its PID
        ffmpeg -i "$FILE" > /dev/null
        FFPID=$!

        # Wait for ffplay to finish naturally
        if wait $FFPID; then
            echo "Successfully played: $FILE"
        else
            # Check if ffplay exited with an error or crashed
            EXIT_STATUS=$?
            echo "Failed to play: $FILE (exit status: $EXIT_STATUS)"
            read -p "uh oh"
        fi

        # Double-check to ensure no lingering ffplay process
        if ps -p $FFPID > /dev/null 2>&1; then
            echo "Cleaning up lingering ffplay process (PID: $FFPID)"
            kill -9 $FFPID
        fi
    fi
done

echo "Processing complete. All processes cleaned up."

