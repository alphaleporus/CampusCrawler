#\!/bin/bash
# Send emails in batches with the new fast timing (20 seconds)

source venv/bin/activate

echo "========================================"
echo "BATCH EMAIL SENDER"
echo "========================================"
echo ""
echo "Settings:"
echo "  - 20 second delay per email"
echo "  - ~23 seconds average with jitter"
echo "  - 50 emails = ~20 minutes"
echo ""

# Use the main script with --live flag
python3 main.py --skip-fetch --skip-crawl --skip-extract --email-limit 50 --live
