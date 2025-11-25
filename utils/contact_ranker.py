"""
Contact Ranking System for University Email Selection.

Implements a 3-tier ranking system to select the best 3 contacts
from potentially dozens of extracted emails per university.
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class EmailScore:
    """Represents a scored email with reasoning."""
    email: str
    score: float
    reason: str
    category: str  # 'HIGH', 'MEDIUM', 'GENERIC', 'EXCLUDED'
    matched_pattern: Optional[str] = None


# ============================================================================
# SCORING RULES
# ============================================================================

# 🚫 BLACKLIST - Automatically exclude these (score: -1.0)
BLACKLIST_PATTERNS = [
    # HR & Employment
    r'^hr@', r'^hroffice@', r'^careers@', r'^jobs@', r'^employment@',
    r'^recruiting@', r'^payroll@', r'^benefits@',

    # IT & Technical Support
    r'^ithelpdesk@', r'^support@', r'^helpdesk@', r'^techsupport@',
    r'^webmaster@', r'^sysadmin@',

    # Operations & Services
    r'^bookstore@', r'^printandcopy@', r'^printing@', r'^mailroom@',
    r'^mailandshipping@', r'^shipping@', r'^receiving@',
    r'^facilities@', r'^maintenance@', r'^operations@',

    # Safety & Security
    r'^police@', r'^safety@', r'^safetyservices@', r'^security@',
    r'^parking@', r'^transportation@',

    # Events & Athletics
    r'^events@', r'^conferencesandevents@', r'^athletics@',
    r'^sports@', r'^tickets@', r'^box[-_]?office@',

    # Housing & Dining
    r'^housing@', r'^residence@', r'^dining@', r'^foodservices@',
    r'^cafeteria@',

    # Marketing & Press
    r'^marketing@', r'^press@', r'^newsroom@', r'^communications@',
    r'^pr@', r'^media@',

    # Finance (not admissions-related)
    r'^accounting@', r'^finance@', r'^bursar@', r'^cashier@',

    # Misc Low-Value
    r'^noreply@', r'^donotreply@', r'^abuse@', r'^spam@',
    r'^postmaster@', r'^webmail@'
]

# 🔥 HIGH PRIORITY (score: 1.00 - 0.90)
HIGH_PRIORITY_PATTERNS = {
    r'^admissions@': (1.00, 'Primary admissions contact'),
    r'^international@': (0.98, 'International student office'),
    r'^global@': (0.97, 'Global programs office'),
    r'^info@': (0.95, 'General information contact'),
    r'^outreach@': (0.95, 'Outreach/recruitment office'),
    r'^welcome@': (0.94, 'Welcome center'),
    r'^registrar@': (0.93, 'Registrar office'),
    r'^studentservices@': (0.92, 'Student services'),
    r'^studentlife@': (0.91, 'Student life office'),
    r'^academic@': (0.90, 'Academic affairs'),
    r'^enroll': (0.96, 'Enrollment office'),
    r'^apply': (0.94, 'Application office'),
}

# ⭐ MEDIUM PRIORITY (score: 0.89 - 0.60)
MEDIUM_PRIORITY_PATTERNS = {
    r'^advising@': (0.85, 'Academic advising'),
    r'^gradadmissions@': (0.84, 'Graduate admissions'),
    r'^undergradadmissions@': (0.84, 'Undergraduate admissions'),
    r'^grad@': (0.82, 'Graduate office'),
    r'^undergraduate@': (0.82, 'Undergraduate office'),
    r'^provost': (0.80, 'Provost office'),
    r'^finaid@': (0.78, 'Financial aid'),
    r'^scholarships@': (0.77, 'Scholarships office'),
    r'^library@': (0.70, 'Library'),
    r'^communitylife@': (0.68, 'Community life'),
    r'^studentaffairs@': (0.85, 'Student affairs'),
    r'^dean': (0.75, 'Dean\'s office'),
    r'^college': (0.65, 'College-level contact'),
    r'^department': (0.63, 'Department contact'),
    r'^program': (0.62, 'Program coordinator'),
}

# 🔹 GENERIC PATTERNS (score: 0.59 - 0.30)
GENERIC_STAFF_PATTERNS = {
    # Named staff (firstname.lastname pattern)
    r'^[a-z]{2,}[._][a-z]{2,}@': (0.45, 'Named staff member'),
    r'^[a-z][a-z0-9]{1,8}@': (0.35, 'Staff email (short username)'),
}

# Keywords that boost scores (additive bonuses)
KEYWORD_BONUSES = {
    'admission': 0.10,
    'international': 0.08,
    'global': 0.08,
    'student': 0.05,
    'info': 0.05,
    'inquiry': 0.07,
    'prospect': 0.08,
    'recruit': 0.07,
    'enroll': 0.09,
    'apply': 0.08,
    'visit': 0.06,
    'tour': 0.05,
}


class ContactRanker:
    """Ranks and selects top 3 contacts from extracted emails."""

    def __init__(self):
        """Initialize the contact ranker."""
        self.blacklist_regex = re.compile('|'.join(BLACKLIST_PATTERNS), re.IGNORECASE)

    def is_blacklisted(self, email: str) -> bool:
        """
        Check if email matches blacklist patterns.
        
        Args:
            email: Email address to check
        
        Returns:
            True if blacklisted, False otherwise
        """
        return bool(self.blacklist_regex.match(email.lower()))

    def calculate_score(self, email: str) -> EmailScore:
        """
        Calculate comprehensive score for an email.
        
        Args:
            email: Email address to score
        
        Returns:
            EmailScore object with score and reasoning
        """
        email_lower = email.lower()

        # Check blacklist first
        if self.is_blacklisted(email):
            return EmailScore(
                email=email,
                score=-1.0,
                reason="Blacklisted pattern",
                category='EXCLUDED',
                matched_pattern=self._find_blacklist_match(email_lower)
            )

        # Check HIGH PRIORITY patterns
        for pattern, (score, reason) in HIGH_PRIORITY_PATTERNS.items():
            if re.match(pattern, email_lower):
                bonus = self._calculate_keyword_bonus(email_lower)
                final_score = min(1.0, score + bonus)  # Cap at 1.0

                return EmailScore(
                    email=email,
                    score=final_score,
                    reason=reason + (f" +bonus({bonus:.2f})" if bonus > 0 else ""),
                    category='HIGH',
                    matched_pattern=pattern
                )

        # Check MEDIUM PRIORITY patterns
        for pattern, (score, reason) in MEDIUM_PRIORITY_PATTERNS.items():
            if re.search(pattern, email_lower):
                bonus = self._calculate_keyword_bonus(email_lower)
                final_score = min(0.89, score + bonus)  # Cap at 0.89

                return EmailScore(
                    email=email,
                    score=final_score,
                    reason=reason + (f" +bonus({bonus:.2f})" if bonus > 0 else ""),
                    category='MEDIUM',
                    matched_pattern=pattern
                )

        # Check GENERIC patterns
        for pattern, (score, reason) in GENERIC_STAFF_PATTERNS.items():
            if re.match(pattern, email_lower):
                bonus = self._calculate_keyword_bonus(email_lower)
                final_score = min(0.59, score + bonus)  # Cap at 0.59

                return EmailScore(
                    email=email,
                    score=final_score,
                    reason=reason + (f" +bonus({bonus:.2f})" if bonus > 0 else ""),
                    category='GENERIC',
                    matched_pattern=pattern
                )

        # Default: unmatched pattern (low score)
        return EmailScore(
            email=email,
            score=0.20,
            reason="Unmatched pattern (low priority)",
            category='GENERIC',
            matched_pattern=None
        )

    def _calculate_keyword_bonus(self, email: str) -> float:
        """Calculate bonus score from keywords in email."""
        bonus = 0.0
        for keyword, bonus_value in KEYWORD_BONUSES.items():
            if keyword in email:
                bonus += bonus_value
        return bonus

    def _find_blacklist_match(self, email: str) -> str:
        """Find which blacklist pattern matched."""
        for pattern in BLACKLIST_PATTERNS:
            if re.match(pattern, email):
                return pattern
        return "unknown"

    def deduplicate_similar(self, scored_emails: List[EmailScore]) -> List[EmailScore]:
        """
        Remove similar/redundant emails.
        
        For example, if we have both:
          - admissions@university.edu (score: 1.0)
          - gradadmissions@university.edu (score: 0.84)
        
        We might keep both, but if we have:
          - info@university.edu (score: 0.95)
          - information@university.edu (score: 0.40)
        
        We'd only keep the higher scored one.
        
        Args:
            scored_emails: List of scored emails
        
        Returns:
            Deduplicated list
        """
        # For now, keep all (deduplication can be added if needed)
        # This is a placeholder for more sophisticated logic
        return scored_emails

    def select_top_3(
            self,
            emails: List[str],
            university_name: str
    ) -> Dict[str, any]:
        """
        Select top 3 contacts from email list.
        
        Args:
            emails: List of email addresses
            university_name: Name of university (for logging)
        
        Returns:
            Dictionary with selection results and metadata
        """
        logger.info(f"🎯 Ranking {len(emails)} emails for {university_name}")

        # Score all emails
        scored_emails = [self.calculate_score(email) for email in emails]

        # Separate excluded from valid
        valid_emails = [s for s in scored_emails if s.score >= 0]
        excluded_emails = [s for s in scored_emails if s.score < 0]

        logger.info(f"   Valid: {len(valid_emails)}, Excluded: {len(excluded_emails)}")

        # Sort by score (descending)
        valid_emails.sort(key=lambda x: x.score, reverse=True)

        # Deduplicate if needed
        valid_emails = self.deduplicate_similar(valid_emails)

        # Select top 3
        primary = valid_emails[0] if len(valid_emails) >= 1 else None
        secondary = valid_emails[1] if len(valid_emails) >= 2 else None
        tertiary = valid_emails[2] if len(valid_emails) >= 3 else None

        # Log selection
        self._log_selection(university_name, primary, secondary, tertiary, excluded_emails)

        return {
            'university': university_name,
            'primary': self._email_score_to_dict(primary) if primary else None,
            'secondary': self._email_score_to_dict(secondary) if secondary else None,
            'tertiary': self._email_score_to_dict(tertiary) if tertiary else None,
            'total_extracted': len(emails),
            'valid_count': len(valid_emails),
            'excluded_count': len(excluded_emails),
            'excluded_emails': [e.email for e in excluded_emails],
            'all_scored': [self._email_score_to_dict(e) for e in valid_emails]
        }

    def _email_score_to_dict(self, email_score: EmailScore) -> Dict:
        """Convert EmailScore to dictionary."""
        return {
            'email': email_score.email,
            'score': email_score.score,
            'reason': email_score.reason,
            'category': email_score.category,
            'pattern': email_score.matched_pattern
        }

    def _log_selection(
            self,
            university: str,
            primary: Optional[EmailScore],
            secondary: Optional[EmailScore],
            tertiary: Optional[EmailScore],
            excluded: List[EmailScore]
    ):
        """Log selection details."""
        logger.info(f"📧 SELECTED CONTACTS for {university}:")

        if primary:
            logger.info(f"   🥇 PRIMARY: {primary.email} (score: {primary.score:.2f}) - {primary.reason}")
        else:
            logger.warning(f"   ⚠️  No primary contact found!")

        if secondary:
            logger.info(f"   🥈 SECONDARY: {secondary.email} (score: {secondary.score:.2f}) - {secondary.reason}")

        if tertiary:
            logger.info(f"   🥉 TERTIARY: {tertiary.email} (score: {tertiary.score:.2f}) - {tertiary.reason}")

        if excluded:
            logger.debug(f"   🚫 EXCLUDED {len(excluded)} emails: {', '.join([e.email for e in excluded[:5]])}")


# Singleton instance
ranker = ContactRanker()
