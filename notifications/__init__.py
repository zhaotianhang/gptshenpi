sent_notifications = []


def send(recipients, message, channels=None):
    """Send a notification to one or more recipients.

    Parameters
    ----------
    recipients : list[int]
        User IDs of the recipients.
    message : str
        Message body of the notification.
    channels : list[str], optional
        Channels to send through. Supported channels are ``in_app``, ``sms``
        and ``third_party``. Defaults to ["in_app"].
    """
    channels = channels or ["in_app"]
    for rid in recipients:
        for ch in channels:
            sent_notifications.append(
                {
                    "recipient_id": rid,
                    "channel": ch,
                    "message": message,
                }
            )


def reset():
    """Clear recorded notifications (useful for tests)."""
    sent_notifications.clear()
