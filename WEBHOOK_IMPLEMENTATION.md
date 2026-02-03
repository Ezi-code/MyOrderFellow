# Webhook System Implementation Guide

## Overview

The webhook system in My Order Fellow is now fully implemented with the following features:

1. **Automatic webhook secret generation on KYC approval**
2. **Signature verification for all webhook requests**
3. **Automatic secret regeneration when expired**
4. **KYC-only access control**

---

## How It Works

### 1. Webhook Secret Generation Flow

```
User Registration
      ↓
OTP Verification & Account Activation
      ↓
KYC Submission
      ↓
Admin KYC Approval (approved = True)
      ↓
Django Signal Triggered
      ↓
WebhookSecret Auto-Generated (90-day expiry)
      ↓
Company Can Now Send Webhooks
```

### 2. Webhook Request Flow

```
E-Commerce Platform
      ↓
  POST /api/v1/webhooks/orders/
  Headers:
    X-API-Key: whsk_xxxxxxxxxxxx
    X-Webhook-Signature: hmac-sha256-signature
      ↓
Django View Receives Request
      ↓
Verify API Key Exists in DB
      ↓
Check if Secret Expired
  ├─ Yes: Regenerate automatically
  └─ No: Continue
      ↓
Verify HMAC-SHA256 Signature
      ↓
Process Order Data
      ↓
Return 201 Created / 400 Bad Request / 401 Unauthorized
```

---

## API Endpoints

### Generate/Get Webhook Secret

**Endpoint:** `POST /api/v1/webhook/secret/`

**Authentication:** Required (User must be logged in)

**Access:** Only KYC-verified users

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/webhook/secret/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json"
```

**Response (201 Created):**
```json
{
  "secret_key": "whsk_abcd1234efgh5678ijkl9012mnop",
  "message": "Store this secret safely. Do not share it. You won't be able to see it again.",
  "status": "created"
}
```

**Error Response (403 Forbidden - Not KYC Verified):**
```json
{
  "error": "KYC approval required",
  "message": "You must complete and have your KYC approved to access webhook functionality."
}
```

---

### Check Webhook Secret Status

**Endpoint:** `GET /api/v1/webhook/secret/`

**Authentication:** Required

**Access:** Only KYC-verified users

**Request:**
```bash
curl -X GET http://localhost:8000/api/v1/webhook/secret/ \
  -H "Authorization: Bearer <access_token>"
```

**Response (200 OK):**
```json
{
  "secret_key": "whsk_abcd1234efgh5678ijkl9012mnop",
  "is_active": true,
  "expires_at": "2026-04-28T12:30:45Z"
}
```

---

### Send Order via Webhook

**Endpoint:** `POST /api/v1/webhooks/orders/`

**Authentication:** Webhook Signature

**No user login required** (authentication via HMAC-SHA256 signature)

**Request:**
```bash
import hmac
import hashlib
import json
import requests

# Your webhook secret (stored securely)
api_key = "whsk_abcd1234efgh5678ijkl9012mnop"

# Order payload
payload = {
  "customer_details": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+2348123456789"
  },
  "item_summary": "iPhone 15 x2, iPad Pro",
  "address": "123 Main St, Lagos, Nigeria",
  "tracking_status": "PENDING"
}

# Convert to JSON bytes
payload_bytes = json.dumps(payload).encode()

# Create HMAC-SHA256 signature
signature = hmac.new(
  api_key.encode(),
  payload_bytes,
  hashlib.sha256
).hexdigest()

# Send webhook request
headers = {
  "X-API-Key": api_key,
  "X-Webhook-Signature": signature,
  "Content-Type": "application/json"
}

response = requests.post(
  "http://localhost:8000/api/v1/webhooks/orders/",
  json=payload,
  headers=headers
)

print(response.json())
# Output:
# {
#   "status": "success",
#   "order_id": "550e8400-e29b-41d4-a716-446655440000"
# }
```

---

## Security Details

### HMAC-SHA256 Signature Verification

The system uses industry-standard HMAC-SHA256 for webhook authentication.

**How Signature is Created:**
```python
import hmac
import hashlib

api_key = "whsk_abcd1234efgh5678ijkl9012mnop"
request_body = b'{"customer_details":...}'

signature = hmac.new(
    api_key.encode(),
    request_body,
    hashlib.sha256
).hexdigest()
```

**How Signature is Verified (Server-Side):**
```python
# Constant-time comparison prevents timing attacks
hmac.compare_digest(received_signature, expected_signature)
```

### Secret Expiry

- Secrets expire after **90 days**
- When a request arrives with an expired secret, the system:
  1. Detects expiry
  2. Automatically regenerates a new secret
  3. Returns error message instructing company to update configuration
  4. New secret is available in the web dashboard

### Automatic Secret Regeneration

When a company's KYC is approved:
1. Django signal `post_save` on UserKYC is triggered
2. System checks if webhook secret exists
3. If expired → regenerate with new 90-day expiry
4. If doesn't exist → create new secret
5. If valid → no action

---

## Model Details

### WebhookSecret Model

```python
class WebhookSecret(TimeStampedModel):
    user = models.OneToOneField(User, ...)  # One secret per company
    secret_key = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField()  # 90-day expiry
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_expired(self):
        """Check if secret is expired"""
        return timezone.now() > self.expires_at

    def regenerate(self):
        """Generate new secret with new expiry"""
        self.secret_key = f"whsk_{secrets.token_urlsafe(32)}"
        self.expires_at = timezone.now() + timedelta(days=90)
        self.save()
```

---

## Workflow Examples

### Example 1: New E-Commerce Company Setup

```
1. Company Admin registers account
   POST /api/v1/users/auth/register/
   → User created (is_active=False)

2. Company verifies email with OTP
   POST /api/v1/users/verify-otp/?email=company@example.com
   → User account activated (is_active=True)

3. Company submits KYC information
   POST /api/v1/kyc/ (endpoint to be created)
   → KYC record created (approved=False)

4. My Order Fellow admin reviews and approves KYC
   Admin Panel → UserKYC → Approve
   → Signal triggered, WebhookSecret auto-generated

5. Company retrieves webhook secret
   GET /api/v1/webhook/secret/
   → Returns secret_key with 90-day expiry

6. Company starts sending orders
   POST /api/v1/webhooks/orders/
   With X-API-Key and X-Webhook-Signature headers
   → Orders received successfully
```

### Example 2: Expired Secret Recovery

```
1. Company's webhook secret expires after 90 days
   Company tries to send order with old secret

2. System detects expiry
   - Regenerates new secret
   - Returns 401 Unauthorized with message:
     "Webhook secret expired. New secret generated.
      Please update your configuration."

3. Company retrieves new secret
   GET /api/v1/webhook/secret/
   → Returns newly generated secret_key

4. Company updates configuration and retries webhook
   POST /api/v1/webhooks/orders/ (with new secret)
   → Orders received successfully
```

---

## Implementation Notes

### Database Changes

A new field was added to WebhookSecret:
- `expires_at` (DateTimeField): Stores expiry timestamp

Migration: `users/migrations/0007_webhooksecret.py`

### Signal Handler

Location: `users/signals.py`

Triggers when UserKYC is saved with `approved=True`:
```python
@receiver(post_save, sender=UserKYC)
def generate_webhook_secret_on_kyc_approval(sender, instance, **kwargs):
    """Auto-generate webhook secret on KYC approval"""
```

### Utility Functions

Location: `users/utils.py`

- `get_or_create_webhook_secret(user)` - Get/create/regenerate secret
- `verify_webhook_signature(api_key, signature, payload)` - Verify requests

---

## Testing

### Test with cURL

```bash
# 1. Register and login
curl -X POST http://localhost:8000/api/v1/users/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testcompany",
    "email": "test@company.com",
    "password": "SecurePass123"
  }'

# 2. Verify OTP (after admin approves KYC)
curl -X POST http://localhost:8000/api/v1/users/verify-otp/?email=test@company.com \
  -H "Content-Type: application/json" \
  -d '{"otp": "123456"}'

# 3. Login
curl -X POST http://localhost:8000/api/v1/users/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@company.com",
    "password": "SecurePass123"
  }'
# Copy the access token from response

# 4. Get webhook secret (after KYC approval)
curl -X GET http://localhost:8000/api/v1/webhook/secret/ \
  -H "Authorization: Bearer <access_token>"

# 5. Send webhook (with signature)
python webhook_client.py  # See example script below
```

### Python Webhook Client Test Script

```python
# webhook_client.py
import hmac
import hashlib
import json
import requests

API_URL = "http://localhost:8000/api/v1/webhooks/orders/"
API_KEY = "whsk_your_secret_here"

payload = {
    "customer_details": {
        "name": "Test Customer",
        "email": "customer@example.com",
        "phone": "+2348123456789"
    },
    "item_summary": "Test Item",
    "address": "Test Address",
    "tracking_status": "PENDING"
}

payload_bytes = json.dumps(payload).encode()
signature = hmac.new(
    API_KEY.encode(),
    payload_bytes,
    hashlib.sha256
).hexdigest()

headers = {
    "X-API-Key": API_KEY,
    "X-Webhook-Signature": signature,
    "Content-Type": "application/json"
}

response = requests.post(API_URL, json=payload, headers=headers)
print(response.status_code)
print(response.json())
```

---

## Troubleshooting

### Issue: "Invalid API key"
- **Cause:** Secret doesn't exist in database
- **Solution:**
  1. Ensure user's KYC is approved
  2. Call `GET /api/v1/webhook/secret/` to generate one
  3. Copy the secret_key exactly (including `whsk_` prefix)

### Issue: "Invalid signature"
- **Cause:** Signature doesn't match payload
- **Solution:**
  1. Verify you're signing the raw request body (not parsed JSON)
  2. Ensure you're using the correct API key
  3. Use HMAC-SHA256 algorithm
  4. Use hexdigest() for signature output

### Issue: "Webhook secret expired"
- **Cause:** Your secret is older than 90 days
- **Solution:**
  1. Call `GET /api/v1/webhook/secret/` to fetch new secret
  2. Update your configuration
  3. Retry webhook request

---

## Security Best Practices

1. ✅ **Store secret securely** - Never commit to version control
2. ✅ **Use environment variables** - Store API key in .env
3. ✅ **Rotate secrets periodically** - Even if not expired
4. ✅ **Don't share secrets** - Generate separate secret per integration
5. ✅ **Monitor signature failures** - Set up alerts
6. ✅ **Use HTTPS only** - In production
7. ✅ **Implement retry logic** - Handle temporary failures
8. ✅ **Log webhook events** - For audit trails

---

## Next Steps

1. Create KYC submission endpoint (POST /api/v1/kyc/)
2. Create KYC approval/rejection endpoints (for admin)
3. Add rate limiting to webhook endpoint
4. Implement webhook event logging
5. Add webhook retry mechanism
6. Create comprehensive API documentation
