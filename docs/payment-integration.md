# Payment Integration

## Overview

This document describes the **Zarinpal payment integration** and wallet transaction flow used in the **Assets** platform. It ensures secure, auditable, and atomic payment operations across user wallets and the external payment gateway.

---

## Payment Gateway: Zarinpal

The system uses **Zarinpal** to handle IRR (Iranian Rial) payments securely via HTTPS with merchant authentication.

### API Endpoints

- **Sandbox** (testing): `https://sandbox.zarinpal.com/pg/v4/payment/`
- **Production** (live): `https://api.zarinpal.com/pg/v4/payment/`

### Credentials & Config

| Environment Variable    | Purpose                                     |
| ----------------------- | ------------------------------------------- |
| `ZARINPAL_MERCHANT_ID`  | Unique merchant identifier                  |
| `ZARINPAL_CALLBACK_URL` | URL where users are redirected post-payment |
| `ZARINPAL_MODE`         | Either `sandbox` or `production`            |

### Integration Flow

1. System sends a **payment request** with amount, description and callback URL.
2. User is redirected to Zarinpal’s payment page.
3. After payment, user returns to callback URL with payment status & authority code.
4. Backend calls Zarinpal’s **verification API** to confirm the transaction.
5. Based on the verification result, system mark the order as successful or failed.

---

## Payment Workflow

### 1. Initiate Transaction

#### Trigger

**`wallet_topup`** — activated when the user initiates a wallet recharge.

#### Process

1. User requests a wallet top-up from the frontend.
2. Backend generates a **unique order ID** and records a pending transaction in the wallet ledger.
3. A `PaymentRequest` is sent to **Zarinpal**, including the following data:

**Example Request**

```json
{
  "merchant_id": "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
  "amount": 500000,
  "description": "Wallet top-up for user #12",
  "callback_url": "https://{host}[:{port}]/api/v1/payments/verify/",
  "metadata": { "user_id": 12, "type": "wallet_topup" }
}
```

**Example Response**

```json
{
  "data": {
    "code": 100,
    "message": "Payment request accepted",
    "authority": "A00000000000000000000000000123456789"
  }
}
```

4. The frontend redirects the user to Zarinpal’s payment page using the `authority` code.

---

### 2. Verify Transaction (Callback)

Once the user completes the payment, Zarinpal redirects to the callback URL with the following parameters:

```
https://{host}[:{port}]/api/v1/payments/verify/?Authority=A00000000000000000000000000123456789&Status=OK
```

The backend then verifies the payment through Zarinpal’s `/PaymentVerification` API.

**Example Request**

```json
{
  "merchant_id": "XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX",
  "amount": 500000,
  "authority": "A00000000000000000000000000123456789"
}
```

**Example Response**

```json
{
  "data": {
    "code": 100,
    "ref_id": 987654321,
    "message": "Transaction verified successfully"
  }
}
```

---

## Error Handling

| Code | Meaning               | Recommended Action               |
| ---- | --------------------- | -------------------------------- |
| 100  | Success               | Payment verified                 |
| 101  | Already Verified      | Ignore duplicate callback        |
| -9   | Invalid Input         | Check parameters                 |
| -22  | Merchant Disabled     | Contact Zarinpal support         |
| -40  | Invalid Merchant ID   | Verify environment configuration |
| -54  | Transaction Not Found | Check authority code and amount  |

All failures trigger notifications and log entries with the full response payload.

---

## Security Practices

- **HMAC-SHA256** signatures used for request verification.
- All credentials are stored as environment variables and **never committed** to Git.
- Callback requests are validated by IP whitelisting and authority verification.
- Each payment request includes anti-replay nonce fields and timestamps.
- SSL/TLS enforced across all payment communications.

---

## Testing in Sandbox Mode

Sandbox responses mimic live transactions and allow testing without real payments (Set `ZARINPAL_SANDBOX=true` in the environment).

Example testing card:

```
Card Number: 6104-3377-7777-7777
Password: 123
CVV2: 111
Expire Date: 12/1404
```

---

## Reconciliation and Reporting

- Daily reconciliation compares local transactions with Zarinpal’s report API.
- Mismatches trigger an automated alert and manual review task.
- Admin dashboard displays summary metrics:
  - Total processed payments
  - Failed/verifications pending
  - Daily transaction volume

---

## Future Enhancements

- Add multi-gateway abstraction for supporting PayPing or IDPay.
- Integrate refund processing and partial settlements.
- Automate invoice generation and email confirmations.
- Expand payment webhooks for real-time notifications.
