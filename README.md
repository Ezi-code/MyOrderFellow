# My Order Fellow

My Order Fellow is a SaaS application designed to help e-commerce companies provide real-time order tracking updates to their customers. The platform integrates with external e-commerce applications via webhooks. Once an order is received, My Order Fellow manages tracking subscriptions, listens for status updates from the e-commerce platform, and relays those updates to end users through notifications.

## Key Features

- **Order Tracking:** Real-time updates for customer orders.
- **Webhook Integration:** Seamless integration with external e-commerce platforms.
- **User Management:** Secure registration and login with JWT authentication.
- **OTP Verification:** Multi-factor authentication using One-Time Passwords for account activation.
- **KYC Management:** Business verification (Know Your Customer) for companies. **Note: User accounts are activated only after KYC approval by an admin.**
- **Webhook Secret Management:** Secure communication with rotated webhook secrets.
- **Automated Notifications:** Relays status updates to end users.
- **API Documentation:** Comprehensive API documentation using Swagger and Redoc.

## Technologies Used

- **Backend:** Python, Django, Django REST Framework.
- **Authentication:** SimpleJWT (JSON Web Tokens).
- **Documentation:** drf-spectacular (OpenAPI 3.0).
- **Task Management:** django-tasks.
- **Database:** SQLite (Development).

## Project Structure

```text
my_order_fellow/
├── base/               # Common abstract models and utilities
├── myOrderFellow/      # Main project configuration (settings, urls, wsgi, asgi)
├── orderReceptions/    # Order management and webhook handling
├── users/              # User management, authentication, KYC, and secrets
├── requirements/       # Dependency files (base, local, production)
├── manage.py           # Django management script
```

## Setup and Installation

### Prerequisites

- Python 3.10+
- pip (Python package installer)
- virtualenv (optional but recommended)

### Installation Steps

1. **Clone the Repository:**
   ```bash
   git clone <repository-url>
   cd my_order_fellow
   ```

2. **Create a Virtual Environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements/local.txt
   ```

4. **Environment Variables:**
   Create a `.env` file in the root directory (or set them in your environment):
   ```env
   WEBHOOK_API_TOKEN=your_secure_token_here
   ```

5. **Run Migrations:**
   ```bash
   python -m manage migrate
   ```

6. **Create a Superuser (Optional):**
   ```bash
   python -m manage createsuperuser
   ```

## Running the Application

1. **Start the Development Server:**
   ```bash
   python -m manage runserver
   ```

2. **Access the API:**
   The API will be available at `http://127.0.0.1:8000/api/v1/`.

> **Note:** For local development, emails (including OTPs) are sent to the console. Check your terminal output after registration or OTP request.

## API Documentation

The project uses `drf-spectacular` for API documentation. Once the server is running, you can access the following:

- **Swagger UI:** `http://127.0.0.1:8000/api/v1/docs/swagger/`
- **Redoc:** `http://127.0.0.1:8000/api/v1/docs/redoc/`
- **Schema (YAML):** `http://127.0.0.1:8000/api/v1/docs/`

## Core API Endpoints

### Authentication & Users
- `POST /api/v1/users/auth/register/`: Register a new user.
- `POST /api/v1/users/verify-otp/`: Verify account via OTP.
- `POST /api/v1/users/request-otp/`: Request a new OTP.
- `POST /api/v1/users/auth/login/`: Login and receive JWT tokens.
- `POST /api/v1/users/auth/logout/`: Blacklist the refresh token and logout.

### Order Receptions
- `POST /api/v1/webhook/`: Webhook endpoint for receiving orders from external services.
- `GET /api/v1/orderreceptions/`: List all orders.
- `GET /api/v1/orderreceptions/{uuid}/`: Retrieve specific order details.

## Account Activation Process

To ensure security and verify businesses, My Order Fellow follows a multi-step activation process:

1.  **Registration:** User registers with email and password.
2.  **Email Verification:** User receives an OTP via email and must verify it. This sets the account as `is_verified`.
3.  **KYC Submission:** The user must provide business details (currently handled via the Admin panel).
4.  **Admin Approval:** An administrator reviews and approves the KYC submission.
5.  **Account Activation:** Upon KYC approval, the user's account is set to `is_active=True`, and a Webhook Secret is automatically generated. Only active accounts can log in and receive webhook data.

## API Examples (Request & Response)

### User Registration
`POST /api/v1/users/auth/register/`

**Request Body:**
```json
{
    "company_name": "johndoe",
    "email": "john@example.com",
    "password": "securepassword123"
}
```

**Response (201 Created):**
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "company_name": "johndoe",
    "email": "john@example.com"
}
```

### OTP Verification
`POST /api/v1/users/verify-otp/`

**Request Body:**
```json
{
    "email": "john@example.com",
    "otp": "123456"
}
```

**Response (200 OK):**
```json
{
    "detail": "OTP verified successfully."
}
```

### Request New OTP
`POST /api/v1/users/request-otp/`

**Request Body:**
```json
{
    "email": "john@example.com"
}
```

**Response (200 OK):**
```json
"OTP sent to your email."
```

### User Login
`POST /api/v1/users/auth/login/`

**Request Body:**
```json
{
    "email": "john@example.com",
    "password": "securepassword123"
}
```

**Response (200 OK):**
```json
{
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "company_name": "johndoe",
    "email": "john@example.com"
}
```

### User Logout
`POST /api/v1/users/auth/logout/`

**Request Body:**
```json
{
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (204 No Content):**
*(No body returned)*

### Webhook Order Reception
`POST /api/v1/webhook/`

**Headers:**
- `X-Webhook-Signature`: `your_secure_token_here`
- `X-Customer-Email`: `john@example.com`

**Request Body:**
```json
{
    "customer_details": {
        "name": "Jane Doe",
        "phone": "+1234567890",
        "email": "jane@example.com"
    },
    "address": "123 Main St, Anytown, USA",
    "item_summary": "1x Widget, 2x Gadgets",
    "tracking_status": "PENDING"
}
```

**Response (201 Created):**
```json
{
    "id": "772f9111-b38c-45a1-9234-112233445566",
    "customer_details": {
        "id": 1,
        "name": "Jane Doe",
        "phone": "+1234567890",
        "email": "jane@example.com"
    },
    "address": "123 Main St, Anytown, USA",
    "item_summary": "1x Widget, 2x Gadgets",
    "tracking_status": "PENDING"
}
```

### List Orders
`GET /api/v1/orderreceptions/`

**Response (200 OK):**
```json
[
    {
        "id": "772f9111-b38c-45a1-9234-112233445566",
        "customer_details": {
            "id": 1,
            "name": "Jane Doe",
            "phone": "+1234567890",
            "email": "jane@example.com"
        },
        "address": "123 Main St, Anytown, USA",
        "item_summary": "1x Widget, 2x Gadgets",
        "tracking_status": "PENDING"
    }
]
```

### Retrieve Order Detail
`GET /api/v1/orderreceptions/{uuid}/`

**Response (200 OK):**
```json
{
    "id": "772f9111-b38c-45a1-9234-112233445566",
    "customer_details": {
        "id": 1,
        "name": "Jane Doe",
        "phone": "+1234567890",
        "email": "jane@example.com"
    },
    "address": "123 Main St, Anytown, USA",
    "item_summary": "1x Widget, 2x Gadgets",
    "tracking_status": "PENDING"
}
```
