import email
import imaplib
import logging
import os
import time
from email.header import decode_header
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=ROOT_DIR / ".env", override=True)


class GmailFetcher:
    """
    Utility to connect to Gmail and fetch delivered notification emails
    for verification in automated tests.
    Targets recipient: abhisheksingh7266833285@gmail.com
    """

    IMAP_SERVER = "imap.gmail.com"
    IMAP_PORT = 993

    def __init__(self, user=None, password_or_token=None):
        self.user = user or os.getenv("GMAIL_USER", "abhisheksingh7266833285@gmail.com")
        self.password_or_token = (
            password_or_token
            or os.getenv("GMAIL_APP_PASSWORD")
            or os.getenv("GMAIL_TOKEN")
            or os.getenv("GMAIL_PASSWORD")
        )
        self.mail = None

    def connect(self):
        """Establish secure SSL connection to Gmail IMAP server."""
        if not self.password_or_token:
            logger.warning(
                "No GMAIL_APP_PASSWORD or GMAIL_TOKEN found in environment. "
                "Set GMAIL_APP_PASSWORD in .env to authenticate with Gmail."
            )
            return False

        try:
            logger.info("Connecting to %s:%d as %s...", self.IMAP_SERVER, self.IMAP_PORT, self.user)
            self.mail = imaplib.IMAP4_SSL(self.IMAP_SERVER, self.IMAP_PORT)
            self.mail.login(self.user, self.password_or_token)
            logger.info("Successfully authenticated to Gmail account: %s", self.user)
            return True
        except Exception as e:
            logger.error("Failed to connect/authenticate to Gmail: %s", str(e))
            self.mail = None
            return False

    def close(self):
        """Close IMAP connection gracefully."""
        if self.mail:
            try:
                self.mail.close()
                self.mail.logout()
            except Exception:
                pass
            self.mail = None

    def _decode_header_value(self, value):
        """Decode MIME encoded email headers."""
        if not value:
            return ""
        decoded_parts = decode_header(value)
        header_text = ""
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                header_text += part.decode(encoding or "utf-8", errors="replace")
            else:
                header_text += str(part)
        return header_text

    def _extract_body(self, msg):
        """Extract plain text and HTML body from email message object."""
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    payload = part.get_payload(decode=True)
                    if payload:
                        body += payload.decode("utf-8", errors="replace")
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                body = payload.decode("utf-8", errors="replace")
        return body

    def fetch_latest_email(self, subject_contains=None, sender_contains=None, since_date=None, timeout=30, poll_interval=3):
        """
        Polls the inbox for the latest email matching criteria.
        
        Args:
            subject_contains (str, optional): Keyword that should be in the subject line.
            sender_contains (str, optional): Keyword that should be in the From header.
            since_date (str, optional): IMAP date filter, e.g., '01-Jan-2026'.
            timeout (int): Max seconds to wait for email to arrive.
            poll_interval (int): Seconds between check attempts.

        Returns:
            dict or None: {
                "id": str,
                "subject": str,
                "from": str,
                "to": str,
                "date": str,
                "body": str,
                "raw_message": email.message.Message
            }
        """
        if not self.mail and not self.connect():
            logger.error("Cannot fetch email without active Gmail connection.")
            return None

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                self.mail.select("INBOX")
                criteria = []
                if since_date:
                    criteria.append(f'(SINCE "{since_date}")')
                if not criteria:
                    criteria.append("ALL")

                search_query = " ".join(criteria)
                status, data = self.mail.search(None, search_query)

                if status == "OK" and data[0]:
                    email_ids = data[0].split()
                    # Iterate from newest to oldest
                    for eid in reversed(email_ids):
                        fetch_status, msg_data = self.mail.fetch(eid, "(RFC822)")
                        if fetch_status != "OK" or not msg_data:
                            continue

                        raw_email = msg_data[0][1]
                        msg = email.message_from_bytes(raw_email)

                        subject = self._decode_header_value(msg.get("Subject", ""))
                        sender = self._decode_header_value(msg.get("From", ""))
                        to = self._decode_header_value(msg.get("To", ""))
                        date_str = self._decode_header_value(msg.get("Date", ""))
                        body = self._extract_body(msg)

                        # Match filters
                        if subject_contains and subject_contains.lower() not in subject.lower():
                            continue
                        if sender_contains and sender_contains.lower() not in sender.lower():
                            continue

                        logger.info(
                            "Found matching email: Subject='%s' | From='%s' | Date='%s'",
                            subject, sender, date_str
                        )
                        return {
                            "id": eid.decode("utf-8") if isinstance(eid, bytes) else str(eid),
                            "subject": subject,
                            "from": sender,
                            "to": to,
                            "date": date_str,
                            "body": body,
                            "raw_message": msg
                        }

                logger.debug("Matching email not found yet, retrying in %ds...", poll_interval)
                time.sleep(poll_interval)

            except Exception as e:
                logger.warning("Error while polling Gmail inbox: %s", str(e))
                time.sleep(poll_interval)

        logger.warning("Timed out after %d seconds waiting for email matching criteria.", timeout)
        return None
