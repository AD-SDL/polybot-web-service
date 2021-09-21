#! /bin/bash

for f in `find 706data -name "*.json"`; do
  # Send data to the web service
  curl -H "Content-Type: application/json" -L --data @${f} http://127.0.0.1:5001/ingest
  echo  # So that we get newlines
  sleep 15
done
