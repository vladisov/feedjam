"""Email service for processing inbound emails into feed items."""

import hashlib
import re
from datetime import datetime

from bs4 import BeautifulSoup

from repository.feed_storage import FeedStorage
from repository.source_storage import SourceStorage
from repository.user_storage import UserStorage
from schemas import FeedItemIn
from schemas.email import InboundEmailPayload
from schemas.sources import SourceIn
from utils.logger import get_logger

logger = get_logger(__name__)

# Max content length for email descriptions
MAX_CONTENT_LENGTH = 5000


class EmailService:
    """Service for handling inbound emails and converting to feed items."""

    def __init__(
        self,
        user_storage: UserStorage,
        source_storage: SourceStorage,
        feed_storage: FeedStorage,
    ) -> None:
        self.user_storage = user_storage
        self.source_storage = source_storage
        self.feed_storage = feed_storage

    def process_inbound_email(self, payload: InboundEmailPayload) -> int | None:
        """Process an inbound email and create a feed item.

        Returns the created feed item ID, or None if processing failed.
        """
        # Extract token from recipient address
        email_token = self._extract_token(payload.to)
        if not email_token:
            logger.warning(f"Invalid recipient address: {payload.to}")
            return None

        # Find user by token
        user = self.user_storage.get_by_email_token(email_token)
        if not user:
            logger.warning(f"No user found for email token: {email_token}")
            return None

        # Get or create source for this sender
        source = self._get_or_create_email_source(payload.from_address, user.id)

        # Parse email into feed item
        feed_item = self._email_to_feed_item(payload, source.name)

        # Save feed item
        self.feed_storage.save_items(source, [feed_item])

        logger.info(f"Created feed item from email: {payload.subject[:50]}...")
        return feed_item.local_id

    def _extract_token(self, recipient: str) -> str | None:
        """Extract email token from recipient address.

        Example: 'abc123@in.feedjam.app' -> 'abc123'
        """
        if "@" not in recipient:
            return None
        return recipient.split("@")[0].lower()

    def _get_or_create_email_source(self, sender_email: str, user_id: int):
        """Get or create a source for email newsletters.

        Creates a unique source per sender email address.
        """
        source_name = self._email_to_source_name(sender_email)

        existing = self.source_storage.get_by_name(source_name)
        if existing:
            return existing

        source_in = SourceIn(
            name=source_name,
            resource_url=f"email://{sender_email}",
            source_type="email",
        )
        return self.source_storage.create(source_in)

    def _email_to_source_name(self, sender_email: str) -> str:
        """Convert sender email to source name.

        Example: 'newsletter@substack.com' -> 'email-newsletter-substack'
        """
        # Extract local part and domain
        local, domain = sender_email.lower().split("@")

        # Clean up domain (remove common suffixes)
        domain_clean = domain.replace(".com", "").replace(".io", "").replace(".co", "")

        # Combine into source name
        return f"email-{local}-{domain_clean}"

    def _email_to_feed_item(
        self, payload: InboundEmailPayload, source_name: str
    ) -> FeedItemIn:
        """Convert email payload to FeedItemIn."""
        content = self._extract_content(payload.html, payload.text)
        local_id = self._generate_local_id(payload)
        title = payload.subject or "No Subject"

        return FeedItemIn(
            title=title,
            link="",
            source_name=source_name,
            local_id=local_id,
            description=content,
            published=payload.date or datetime.now(),
        )

    def _extract_content(self, html: str | None, text: str | None) -> str:
        """Extract readable content from email body. Prefers HTML over plain text."""
        if html:
            return self._clean_html(html)
        return text[:MAX_CONTENT_LENGTH] if text else ""

    def _clean_html(self, html: str) -> str:
        """Clean HTML email content for display.

        Removes scripts, styles, and extracts text while preserving links.
        """
        try:
            soup = BeautifulSoup(html, "html.parser")

            # Remove unwanted elements
            for element in soup(["script", "style", "head", "meta"]):
                element.decompose()

            # Get text content
            text = soup.get_text(separator=" ", strip=True)

            # Clean up whitespace
            text = re.sub(r"\s+", " ", text).strip()

            return text[:MAX_CONTENT_LENGTH]
        except Exception as e:
            logger.warning(f"Error cleaning HTML: {e}")
            return html[:MAX_CONTENT_LENGTH] if html else ""

    def _generate_local_id(self, payload: InboundEmailPayload) -> str:
        """Generate a unique local ID for the email."""
        unique_str = f"{payload.from_address}:{payload.subject}:{payload.date}"
        return hashlib.md5(unique_str.encode()).hexdigest()[:16]
