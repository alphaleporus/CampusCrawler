#!/usr/bin/env python3
"""
Test Contact Ranking System

Demonstrates the 3-tier ranking with California Baptist University example
and other test cases.
"""

from utils.contact_ranker import ranker
import json

# California Baptist University - 50+ emails example
cbu_emails = [
    "nursing@calbaptist.edu",
    "jmontgomery@calbaptist.edu",
    "registrar@calbaptist.edu",
    "advising@calbaptist.edu",
    "studentaccounts@calbaptist.edu",
    "conferencesandevents@calbaptist.edu",
    "safetyservices@calbaptist.edu",
    "admissions@calbaptist.edu",
    "international@calbaptist.edu",
    "info@calbaptist.edu",
    "library@calbaptist.edu",
    "finaid@calbaptist.edu",
    "hr@calbaptist.edu",
    "careers@calbaptist.edu",
    "athletics@calbaptist.edu",
    "housing@calbaptist.edu",
    "bookstore@calbaptist.edu",
    "ithelpdesk@calbaptist.edu",
    "gradadmissions@calbaptist.edu",
    "studentservices@calbaptist.edu",
    "provost@calbaptist.edu",
    "dean.engineering@calbaptist.edu",
    "welcome@calbaptist.edu",
    "outreach@calbaptist.edu",
    "printandcopy@calbaptist.edu",
    "police@calbaptist.edu",
]


def test_california_baptist():
    """Test with California Baptist University example."""
    print("=" * 80)
    print("TEST: California Baptist University")
    print("=" * 80)
    print()

    result = ranker.select_top_3(cbu_emails, "California Baptist University")

    print("\n" + "=" * 80)
    print("RESULTS:")
    print("=" * 80)
    print(f"\nTotal Emails Extracted: {result['total_extracted']}")
    print(f"Valid Emails: {result['valid_count']}")
    print(f"Excluded Emails: {result['excluded_count']}")
    print()

    print("🎯 SELECTED TOP 3:")
    print("-" * 80)

    if result['primary']:
        print(f"\n🥇 PRIMARY:")
        print(f"   Email: {result['primary']['email']}")
        print(f"   Score: {result['primary']['score']:.2f}")
        print(f"   Reason: {result['primary']['reason']}")
        print(f"   Category: {result['primary']['category']}")

    if result['secondary']:
        print(f"\n🥈 SECONDARY:")
        print(f"   Email: {result['secondary']['email']}")
        print(f"   Score: {result['secondary']['score']:.2f}")
        print(f"   Reason: {result['secondary']['reason']}")
        print(f"   Category: {result['secondary']['category']}")

    if result['tertiary']:
        print(f"\n🥉 TERTIARY:")
        print(f"   Email: {result['tertiary']['email']}")
        print(f"   Score: {result['tertiary']['score']:.2f}")
        print(f"   Reason: {result['tertiary']['reason']}")
        print(f"   Category: {result['tertiary']['category']}")

    print("\n" + "-" * 80)
    print("🚫 EXCLUDED EMAILS:")
    print("-" * 80)
    for email in result['excluded_emails']:
        print(f"   ✗ {email}")

    print("\n" + "-" * 80)
    print("📊 ALL VALID EMAILS (Top 10 by score):")
    print("-" * 80)
    for i, scored in enumerate(result['all_scored'][:10], 1):
        print(f"   {i}. {scored['email']:40s} | Score: {scored['score']:.2f} | {scored['reason']}")

    return result


def test_scoring_examples():
    """Test individual email scoring."""
    print("\n\n" + "=" * 80)
    print("TEST: Individual Email Scoring Examples")
    print("=" * 80)
    print()

    test_emails = [
        "admissions@university.edu",
        "international@university.edu",
        "info@university.edu",
        "gradadmissions@university.edu",
        "john.doe@university.edu",
        "hr@university.edu",
        "careers@university.edu",
        "athletics@university.edu",
        "library@university.edu",
        "registrar@university.edu",
        "enrollmentservices@university.edu",
        "safetyservices@university.edu",
        "bookstore@university.edu"
    ]

    print(f"{'Email':<50} | {'Score':>6} | {'Category':<10} | Reason")
    print("-" * 120)

    for email in test_emails:
        score = ranker.calculate_score(email)
        status = "✓" if score.score >= 0 else "✗"
        print(f"{status} {email:<47} | {score.score:>6.2f} | {score.category:<10} | {score.reason}")


def test_multiple_universities():
    """Test with multiple universities."""
    print("\n\n" + "=" * 80)
    print("TEST: Multiple Universities")
    print("=" * 80)
    print()

    test_cases = {
        "MIT": [
            "admissions@mit.edu",
            "international@mit.edu",
            "hr@mit.edu",
            "careers@mit.edu",
            "library@mit.edu"
        ],
        "Stanford": [
            "info@stanford.edu",
            "gradadmissions@stanford.edu",
            "studentaffairs@stanford.edu",
            "athletics@stanford.edu",
            "bookstore@stanford.edu"
        ]
    }

    for uni_name, emails in test_cases.items():
        print(f"\n🎓 {uni_name}:")
        print("-" * 40)
        result = ranker.select_top_3(emails, uni_name)

        if result['primary']:
            print(f"   Primary: {result['primary']['email']} ({result['primary']['score']:.2f})")
        if result['secondary']:
            print(f"   Secondary: {result['secondary']['email']} ({result['secondary']['score']:.2f})")
        if result['tertiary']:
            print(f"   Tertiary: {result['tertiary']['email']} ({result['tertiary']['score']:.2f})")


def export_results_json(result):
    """Export results to JSON."""
    print("\n\n" + "=" * 80)
    print("JSON OUTPUT (for database integration):")
    print("=" * 80)
    print()
    print(json.dumps({
        'university': result['university'],
        'contacts': {
            'primary': result['primary'],
            'secondary': result['secondary'],
            'tertiary': result['tertiary']
        },
        'stats': {
            'total_extracted': result['total_extracted'],
            'valid': result['valid_count'],
            'excluded': result['excluded_count']
        }
    }, indent=2))


if __name__ == "__main__":
    # Run all tests
    result = test_california_baptist()
    test_scoring_examples()
    test_multiple_universities()
    export_results_json(result)

    print("\n\n" + "=" * 80)
    print("✅ ALL TESTS COMPLETE")
    print("=" * 80)
