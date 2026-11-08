#!/usr/bin/env python3
import json
import os
from datetime import datetime

TRACKER_FILE = '/opt/data/profiles/english-class/tracker.json'

def advance_day():
    if not os.path.exists(TRACKER_FILE):
        return
    with open(TRACKER_FILE, 'r') as f:
        tracker = json.load(f)

    # If start_date not set, set it today
    if not tracker.get('start_date'):
        tracker['start_date'] = datetime.now().strftime('%Y-%m-%d')

    curr = tracker.get('current_day', 1)
    if curr not in tracker.get('completed_days', []):
        tracker.setdefault('completed_days', []).append(curr)

    if curr < 30:
        tracker['current_day'] = curr + 1
        tracker['current_week'] = ((tracker['current_day'] - 1) // 7) + 1

    with open(TRACKER_FILE, 'w') as f:
        json.dump(tracker, f, indent=2, ensure_ascii=False)
    print(f"Advanced to Day {tracker['current_day']} (Week {tracker['current_week']})")

if __name__ == '__main__':
    advance_day()
