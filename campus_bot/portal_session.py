import time
import requests


SESSION_DURATION = 10 * 60  # 10 minutes


class PortalSession:
    """Stores a temporary authenticated portal session."""

    def __init__(self, session):
        self.session = session
        self.created_at = time.time()

    @property
    def is_expired(self):
        return (
            time.time() - self.created_at
        ) >= SESSION_DURATION


class PortalSessionManager:
    """Manages temporary portal sessions."""

    def __init__(self):
        self._sessions = {}

    def create_session(self, telegram_id, session):
        """
        Store a new authenticated portal session.
        """

        # Remove existing session if present
        self.remove_session(telegram_id)

        self._sessions[telegram_id] = PortalSession(
            session
        )

    def get_session(self, telegram_id):
        """
        Return an active session.

        Returns None if the session doesn't exist
        or has expired.
        """

        portal_session = self._sessions.get(
            telegram_id
        )

        if portal_session is None:
            return None

        if portal_session.is_expired:
            self.remove_session(telegram_id)
            return None

        return portal_session.session

    def remove_session(self, telegram_id):
        """
        Remove and close a user's portal session.
        """

        portal_session = self._sessions.pop(
            telegram_id,
            None
        )

        if portal_session:
            portal_session.session.close()

    def clear_expired_sessions(self):
        """
        Remove all expired sessions.
        """

        expired_users = [
            telegram_id
            for telegram_id, portal_session
            in self._sessions.items()
            if portal_session.is_expired
        ]

        for telegram_id in expired_users:
            self.remove_session(telegram_id)


# Global session manager
portal_session_manager = PortalSessionManager()