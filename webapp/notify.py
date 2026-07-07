from notifications_python_client.notifications import NotificationsAPIClient

from case_management.settings import NOTIFY_API_KEY

notify_client = None
if NOTIFY_API_KEY:
    notify_client = NotificationsAPIClient(NOTIFY_API_KEY)


def send_email(
    email_address: str,
    template_id: str,
    personalisation: dict | None = None,
) -> None:
    if notify_client is None:
        raise RuntimeError("NOTIFY_API_KEY is not set")

    notify_client.send_email_notification(
        email_address=email_address,
        template_id=template_id,
        personalisation=personalisation,
    )
