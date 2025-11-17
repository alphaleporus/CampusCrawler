"""
Email template generation with personalization.

Creates polite, personalized emails for university outreach.
"""

from typing import Optional

import config
from utils.logger import setup_logger

logger = setup_logger(__name__)

SUBJECT_TEMPLATE = "Request for University Brochure / Stickers for Student Project"

BODY_TEMPLATE = """Dear {recipient_name},

I hope you're doing well.

My name is Gaurav Sharma, and I'm a Computer Engineering student from India. I've always been very curious about how universities around the world work, and recently I started a small personal project to learn more about different institutions, their culture, and their academic environments.

I'm also trying to help a few of my friends who are prospective graduate and research students explore international universities, so I've been collecting brochures, prospectuses, and informational materials to better understand what each institution offers.

If it's not too much trouble, I would be really grateful if you could share any of the following:

• A brochure or prospectus
• Stickers, flags, or small merch items (if available)
• Any materials for international or graduate students

Apart from learning, I genuinely enjoy the idea of cultural exchange — receiving something from a place so far from mine feels really special, and helps me learn a little bit about your community and campus spirit.

Here is my mailing address:

{sender_address}

Thank you so much for taking the time to read this. I truly appreciate any help or material you're able to share.
Wishing you a wonderful day ahead!

Warm regards,
{sender_name}"""


def generate_recipient_name(email: str) -> str:
    """
    Generate appropriate recipient name from email address.
    
    Args:
        email: Email address
    
    Returns:
        Personalized recipient name
    """
    email_lower = email.lower()

    prefix_to_name = {
        'admissions@': 'Admissions Team',
        'info@': 'Information Office',
        'international@': 'International Office',
        'contact@': 'Contact Team',
        'outreach@': 'Outreach Team',
        'global@': 'Global Programs Office',
        'graduate@': 'Graduate Admissions',
        'undergrad@': 'Undergraduate Admissions',
        'admission@': 'Admissions Office'
    }

    for prefix, name in prefix_to_name.items():
        if email_lower.startswith(prefix):
            return name

    # Default fallback
    return "Admissions Team"


def generate_email(
        university_name: str,
        recipient_email: str,
        sender_name: Optional[str] = None,
        sender_address: Optional[str] = None
) -> tuple[str, str]:
    """
    Generate personalized email subject and body.
    
    Args:
        university_name: Name of the university
        recipient_email: Recipient's email address
        sender_name: Sender's name (defaults to config)
        sender_address: Sender's mailing address (defaults to config)
    
    Returns:
        Tuple of (subject, body)
    """
    if sender_name is None:
        sender_name = config.SENDER_INFO['name']

    if sender_address is None:
        sender_address = config.SENDER_INFO['address']

    recipient_name = generate_recipient_name(recipient_email)

    subject = SUBJECT_TEMPLATE

    body = BODY_TEMPLATE.format(
        recipient_name=recipient_name,
        university_name=university_name,
        sender_name=sender_name,
        sender_address=sender_address
    )

    # Sanity check
    if len(body) < 50:
        raise ValueError(f"Generated email body is too short: {len(body)} chars")

    logger.debug(f"Generated email for {university_name} to {recipient_email}")

    return subject, body


def preview_email(university_name: str, recipient_email: str) -> None:
    """
    Print email preview to console.
    
    Args:
        university_name: Name of the university
        recipient_email: Recipient's email address
    """
    subject, body = generate_email(university_name, recipient_email)

    print("=" * 80)
    print(f"TO: {recipient_email}")
    print(f"SUBJECT: {subject}")
    print("=" * 80)
    print(body)
    print("=" * 80)
