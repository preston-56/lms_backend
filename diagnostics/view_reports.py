#!/usr/bin/env python3
"""
Simple script to view LMS activity diagnostic reports.
Lists available reports and allows viewing a specific report.
"""

import os
import sys
from datetime import datetime

# Define the Report directory
BASE_DIR = os.path.expanduser("~/lms_backend/diagnostics")
REPORT_DIR = os.path.join(BASE_DIR, "lms_reports")

def get_report_files():
    """Return sorted list of .txt reports, newest first."""
    if not os.path.isdir(REPORT_DIR):
        raise FileNotFoundError(f"Report directory not found: {REPORT_DIR}")

    reports = [f for f in os.listdir(REPORT_DIR) if f.endswith('.txt')]
    return sorted(reports, reverse=True)

def format_timestamp_from_filename(filename):
    """
    Extract and format timestamp from filename.
    Expected format: activity_report_YYYYMMDD_HHMMSS.txt
    """
    try:
        parts = filename.rstrip(".txt").split('_')
        date_str, time_str = parts[2], parts[3]
        dt = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (IndexError, ValueError):
        return "Unknown Timestamp"

def list_reports():
    """List all available reports with timestamps."""
    try:
        reports = get_report_files()
        if not reports:
            print("No reports found.")
            return

        print(f"\nAvailable Activity Reports ({len(reports)} found):")
        print("-" * 50)

        for i, report in enumerate(reports, 1):
            timestamp = format_timestamp_from_filename(report)
            print(f"{i}. Report from {timestamp}")

        print("-" * 50)
    except Exception as e:
        print(f"[ERROR] Failed to list reports: {e}")

def view_report(report_number=None):
    """View a specific report by number or the latest if none specified."""
    try:
        reports = get_report_files()
        if not reports:
            print("No reports found.")
            return

        index = 0 if report_number is None else report_number - 1
        if not (0 <= index < len(reports)):
            print(f"Invalid report number: {report_number}")
            return

        report_file = reports[index]
        report_path = os.path.join(REPORT_DIR, report_file)

        with open(report_path, 'r') as f:
            content = f.read()

        print("\n" + "=" * 70)
        print(f"REPORT: {report_file}")
        print("=" * 70 + "\n")
        print(content)
        print("\n" + "=" * 70)
        print(f"End of report: {report_path}")
        print("=" * 70)

    except Exception as e:
        print(f"[ERROR] Failed to read report: {e}")

def main():
    """Main CLI entrypoint."""
    if len(sys.argv) > 1:
        try:
            report_num = int(sys.argv[1])
            view_report(report_num)
        except ValueError:
            print(f"[ERROR] Invalid argument: {sys.argv[1]}")
            print("Usage: view_reports.py [report_number]")
    else:
        list_reports()
        print("\nTo view a specific report: view_reports.py <report_number>")
        print("To view the latest report: view_reports.py 1")

if __name__ == "__main__":
    main()
