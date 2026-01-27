# Authentication Service API

The Authentication Service handles user registration, login, session management (JWT), and profile retrieval.

## Base URL
`/api/v1/auth`

## Endpoints

### 1. Register User
Create a new user account.

- **URL**: `/register`
- **Method**: `POST`
- **Auth Required**: No

#### Request Body (`UserCreate`)
| Field | Type | Required | Description |
|---|---|---|---|
| `email` | string (email) | Yes | Valid email address (must be unique) |
| `password` | string | Yes | Min 8 chars, 1 uppercase, 1 lowercase, 1 digit |
| `full_name` | string | Yes | User's full name in English |
| `full_name_gujarati` | string | No | User's full name in Gujarati |
| `phone` | string | No | Phone number |
| `language_preference` | enum | No | `gu` (default), `en`, `gu-en` |
| `grade_level` | string | No | Student's grade level |
| `institution_id` | UUID | No | ID of associated institution |

#### Response (`AuthResponse`)
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "full_name": "John Doe",
      "role": { "name": "student" },
      ...
    },
    "tokens": {
      "access_token": "jwt_token...",
      "refresh_token": "jwt_token...",
      "token_type": "bearer",
      "expires_in": 3600
    }
  }
}
```

### 2. Login
Authenticate user and receive JWT tokens.

- **URL**: `/login`
- **Method**: `POST`
- **Auth Required**: No

#### Request Body (`UserLogin`)
| Field | Type | Required | Description |
|---|---|---|---|
| `email` | string (email) | Yes | Registered email |
| `password` | string | Yes | Password |

#### Response (`AuthResponse`)
Same as Register.

### 3. Refresh Token
Get a new access token using a valid refresh token.

- **URL**: `/refresh`
- **Method**: `POST`
- **Auth Required**: No

#### Request Body (`TokenRefresh`)
| Field | Type | Required | Description |
|---|---|---|---|
| `refresh_token` | string | Yes | Long-lived refresh token |

#### Response (`TokenResponse`)
```json
{
  "success": true,
  "data": {
    "access_token": "new_jwt_token...",
    "refresh_token": "new_refresh_token...",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

### 4. Get Current User
Get the profile of the currently authenticated user.

- **URL**: `/me`
- **Method**: `GET`
- **Auth Required**: Yes (Bearer Token)

#### Response (`UserResponse`)
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    ...
  }
}
```

### 5. Logout
Invalidate the current refresh token.

- **URL**: `/logout`
- **Method**: `POST`
- **Auth Required**: Yes

#### Request Body (`TokenRefresh`)
| Field | Type | Required | Description |
|---|---|---|---|
| `refresh_token` | string | Yes | Token to invalidate |

### 6. Logout All
Invalidate ALL sessions for the current user.

- **URL**: `/logout-all`
- **Method**: `POST`
- **Auth Required**: Yes
