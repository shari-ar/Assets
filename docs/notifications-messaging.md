# Notifications & Messaging

## Overview

The **Assets** platform includes a comprehensive **Notifications & Messaging** subsystem that delivers real-time and asynchronous updates to users. It supports multiple communication channels—**SMS**, **WhatsApp**, and **Email**—to ensure high engagement and transparency throughout the asset lending process.

---

## Goals

- Provide timely and reliable notifications to users.
- Support multi-channel delivery (SMS, WhatsApp, Email).
- Allow admin and automated system alerts.
- Enable retry mechanisms for failed messages.
- Maintain auditable logs for compliance and debugging.

---

## Features

- Multi-channel support (Email, SMS, WhatsApp).
- Configurable message templates with dynamic data.
- Centralized logging and retry on failure.
- Background job processing with Celery.
- Admin control for broadcasting messages.

---

## Notification Flow

1. **Event Triggered** – A system action (e.g., payment verified, ticket approved) triggers a notification.
2. **Message Created** – The backend generates a `Notification` record with placeholders and metadata.
3. **Queue Dispatch** – Message is queued in Celery and sent asynchronously.
4. **Delivery Attempt** – The appropriate adapter (SMS, WhatsApp, Email) processes and sends it.
5. **Status Update** – On success or failure, the record is updated with a timestamp and provider response.

---

## Database Schema

| Column       | Type                             | Description          |
| ------------ | -------------------------------- | -------------------- |
| `id`         | SERIAL                           | Primary key          |
| `user_id`    | INT (FK → users.id)              | Target recipient     |
| `channel`    | ENUM('sms', 'whatsapp', 'email') | Delivery medium      |
| `message`    | TEXT                             | Full message content |
| `status`     | ENUM('queued','sent','failed')   | Delivery state       |
| `created_at` | TIMESTAMP                        | Time created         |
| `sent_at`    | TIMESTAMP                        | Time sent            |
| `error_log`  | TEXT                             | Error details if any |

**Indexes:**

- `idx_notifications_user`
- `idx_notifications_status`

---

## Message Templates

Templates are stored as Markdown files and rendered with variables using Django’s `Template` engine.

**Example Template (`templates/notifications/ticket_accepted.txt`):**

```
Hello {{ user.first_name }},

Your lending request for "{{ ticket.asset_name }}" has been accepted.
The payment of {{ ticket.price }} IRR has been processed successfully.

Ticket ID: {{ ticket.id }}
Status: {{ ticket.status }}

Thank you for using Assets Platform!
```

**Render Example:**

```python
from django.template.loader import render_to_string

message = render_to_string("notifications/ticket_accepted.txt", {
    "user": user,
    "ticket": ticket
})
```

---

## Channels

### 1. Email

- Sent via **Postmark**.
- Supports HTML templates and attachments.
- Utilizes Django’s built-in email backend with async wrappers.

**Example:**

```python
from django.core.mail import send_mail

send_mail(
    subject="Ticket Approved",
    message=message_text,
    from_email="no-reply@assets.example.com",
    recipient_list=[user.email]
)
```

### 2. SMS

- Integrates with [**sms.ir**](https://sms.ir/).
- Short messages for transaction and verification updates.

**Example SMS Payload:**

```json
{
  "receptor": "+989123456789",
  "message": "Your ticket #42 has been approved."
}
```

### 3. WhatsApp

- Uses Twilio for message delivery.
- Supports template-based and custom messages.
- Requires verified business account and webhook setup.

**Example:**

```python
import requests

requests.post("https://graph.facebook.com/v17.0/<phone_id>/messages", json={
  "messaging_product": "whatsapp",
  "to": "+989123456789",
  "type": "text",
  "text": {"body": "Your wallet has been credited with 100,000 IRR."}
})
```

---

## Configuration

All notification services are configured via environment variables and Docker Secrets.

---

## Background Processing (Celery)

Notifications are sent asynchronously to improve response times.

---

## Admin Interface

- Admins can resend failed notifications.
- Dashboard metrics display delivery rates and errors.
- Filters available for date, channel, and status.

---

## Testing Notifications

Use **Django’s Email Backend Debug Mode** for local testing:

```
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
```

To test SMS and WhatsApp locally, mock provider APIs using **responses**.

---

## Logging & Monitoring

- All events stored in the `notifications` table.
- Failures logged in Django’s log system and sent to **Sentry**.
- Prometheus metrics track delivery latency and failure rates.

**Example Metric Labels:**

```
notifications_sent_total{channel="email"}
notifications_failed_total{channel="sms"}
notifications_latency_seconds{channel="whatsapp"}
```

---

## Future Enhancements

- Push notification support (Firebase Cloud Messaging).
- User preference center for notification settings.
- Delivery analytics dashboard.
- Multi-language template system.
- AI-based message personalization.
