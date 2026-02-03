# Webhook System - Quick Reference

## For E-Commerce Company

### Step 1: Get Webhook Secret

```bash
# After KYC is approved and you're logged in:
curl -X GET http://localhost:8000/api/v1/webhook/secret/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Response:
{
  "secret_key": "whsk_abcd1234efgh5678ijkl9012mnop",
  "is_active": true,
  "expires_at": "2026-04-28T12:30:45Z"
}
```

### Step 2: Create HMAC Signature

```python
import hmac
import hashlib
import json

api_key = "whsk_abcd1234efgh5678ijkl9012mnop"
payload = {
  "customer_details": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+2348123456789"
  },
  "item_summary": "Order items",
  "address": "Delivery address",
  "tracking_status": "PENDING"
}

# Create signature
payload_bytes = json.dumps(payload).encode()
signature = hmac.new(
  api_key.encode(),
  payload_bytes,
  hashlib.sha256
).hexdigest()
```

### Step 3: Send Order

```bash
curl -X POST http://localhost:8000/api/v1/webhooks/orders/ \
  -H "X-API-Key: whsk_abcd1234efgh5678ijkl9012mnop" \
  -H "X-Webhook-Signature: <signature_from_step_2>" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_details": {
      "name": "John Doe",
      "email": "john@example.com",
      "phone": "+2348123456789"
    },
    "item_summary": "Order items",
    "address": "Delivery address",
    "tracking_status": "PENDING"
  }'

# Response (201 Created):
{
  "status": "success",
  "order_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

## For Admin

### Approve KYC to Enable Webhooks

1. Go to Django Admin: `http://localhost:8000/admin/`
2. Navigate to: Users → User KYC
3. Find the company's KYC record
4. Check the "Approved" checkbox
5. Click "Save"
6. → Webhook secret is **automatically generated**

### Check Generated Secret (Optional)

```bash
# Admin can view in Django admin:
# Users → Webhook Secrets

# Or via API (if logged in as admin):
curl -X GET http://localhost:8000/api/v1/webhook/secret/ \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

---

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `{"error": "KYC approval required"}` | User not KYC-verified | Have admin approve KYC |
| `{"error": "Invalid API key"}` | Secret doesn't exist in DB | Get secret via GET /webhook/secret/ |
| `{"error": "Invalid signature"}` | Signature doesn't match | Check HMAC-SHA256 calculation |
| `{"error": "Webhook secret expired..."}` | Secret older than 90 days | Fetch new secret via GET /webhook/secret/ |
| `{"error": "Missing authentication headers"}` | Missing X-API-Key or X-Webhook-Signature | Add both headers to request |

---

## Code Examples

### Python - Full Example

```python
import hmac
import hashlib
import json
import requests

class WebhookClient:
    def __init__(self, api_key, webhook_url="http://localhost:8000/api/v1/webhooks/orders/"):
        self.api_key = api_key
        self.webhook_url = webhook_url

    def send_order(self, customer_details, item_summary, address, tracking_status="PENDING"):
        payload = {
            "customer_details": customer_details,
            "item_summary": item_summary,
            "address": address,
            "tracking_status": tracking_status
        }

        # Create signature
        payload_bytes = json.dumps(payload).encode()
        signature = hmac.new(
            self.api_key.encode(),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()

        # Send request
        headers = {
            "X-API-Key": self.api_key,
            "X-Webhook-Signature": signature,
            "Content-Type": "application/json"
        }

        response = requests.post(self.webhook_url, json=payload, headers=headers)
        return response.json(), response.status_code

# Usage
client = WebhookClient(api_key="whsk_your_secret_here")

customer = {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+2348123456789"
}

result, status = client.send_order(
    customer_details=customer,
    item_summary="iPhone 15 x2",
    address="123 Main St, Lagos",
    tracking_status="PENDING"
)

print(f"Status: {status}")
print(f"Response: {result}")
```

### JavaScript/Node.js Example

```javascript
const crypto = require('crypto');
const axios = require('axios');

class WebhookClient {
  constructor(apiKey, webhookUrl = 'http://localhost:8000/api/v1/webhooks/orders/') {
    this.apiKey = apiKey;
    this.webhookUrl = webhookUrl;
  }

  createSignature(payload) {
    const payloadBytes = JSON.stringify(payload);
    const signature = crypto
      .createHmac('sha256', this.apiKey)
      .update(payloadBytes)
      .digest('hex');
    return signature;
  }

  async sendOrder(customerDetails, itemSummary, address, trackingStatus = 'PENDING') {
    const payload = {
      customer_details: customerDetails,
      item_summary: itemSummary,
      address: address,
      tracking_status: trackingStatus
    };

    const signature = this.createSignature(payload);

    try {
      const response = await axios.post(this.webhookUrl, payload, {
        headers: {
          'X-API-Key': this.apiKey,
          'X-Webhook-Signature': signature,
          'Content-Type': 'application/json'
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error:', error.response?.data || error.message);
      throw error;
    }
  }
}

// Usage
const client = new WebhookClient('whsk_your_secret_here');

client.sendOrder(
  { name: 'John Doe', email: 'john@example.com', phone: '+2348123456789' },
  'iPhone 15 x2',
  '123 Main St, Lagos'
).then(result => console.log('Success:', result));
```

### PHP Example

```php
<?php

class WebhookClient {
    private $apiKey;
    private $webhookUrl;

    public function __construct($apiKey, $webhookUrl = 'http://localhost:8000/api/v1/webhooks/orders/') {
        $this->apiKey = $apiKey;
        $this->webhookUrl = $webhookUrl;
    }

    private function createSignature($payload) {
        $payloadJson = json_encode($payload);
        $signature = hash_hmac('sha256', $payloadJson, $this->apiKey, false);
        return $signature;
    }

    public function sendOrder($customerDetails, $itemSummary, $address, $trackingStatus = 'PENDING') {
        $payload = [
            'customer_details' => $customerDetails,
            'item_summary' => $itemSummary,
            'address' => $address,
            'tracking_status' => $trackingStatus
        ];

        $signature = $this->createSignature($payload);

        $ch = curl_init($this->webhookUrl);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($payload));
        curl_setopt($ch, CURLOPT_HTTPHEADER, [
            'X-API-Key: ' . $this->apiKey,
            'X-Webhook-Signature: ' . $signature,
            'Content-Type: application/json'
        ]);

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        return [
            'data' => json_decode($response, true),
            'status' => $httpCode
        ];
    }
}

// Usage
$client = new WebhookClient('whsk_your_secret_here');

$result = $client->sendOrder(
    ['name' => 'John Doe', 'email' => 'john@example.com', 'phone' => '+2348123456789'],
    'iPhone 15 x2',
    '123 Main St, Lagos'
);

echo json_encode($result);
?>
```

---

## Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 201 | Order Created | Success ✅ |
| 400 | Bad Request | Check payload format |
| 401 | Unauthorized | Check API key and signature |
| 403 | Forbidden | KYC not approved yet |
| 500 | Server Error | Contact support |

---

## Headers Required

```
X-API-Key: whsk_xxxxxxxxxxxxx          # Your webhook secret
X-Webhook-Signature: hexdigest         # HMAC-SHA256 of payload
Content-Type: application/json         # Request format
```

---

## Secret Prefix

All secrets start with `whsk_` to identify them as webhook secrets:
- `whsk_abcd1234efgh5678ijkl9012mnop` ✅ Valid
- `my_secret_key` ❌ Invalid (won't work)

---

## Endpoint Map

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| POST | `/api/v1/users/auth/register/` | Register company | None |
| POST | `/api/v1/users/verify-otp/` | Verify email | None |
| POST | `/api/v1/users/auth/login/` | Login | None |
| GET/POST | `/api/v1/webhook/secret/` | Get/create secret | Bearer token |
| POST | `/api/v1/webhooks/orders/` | Send order | HMAC-SHA256 |
