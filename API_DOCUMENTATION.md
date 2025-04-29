# SSO System API Documentation

## Overview

This document provides information about the REST API endpoints available in our Single Sign-On (SSO) system.

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. Most endpoints require a valid access token.

### Token Structure

Authentication uses two tokens:

1. **Access Token**: Short-lived token (15 minutes) used to authenticate API requests
2. **Refresh Token**: Long-lived token (7 days) used to get a new access token when the current one expires

## Base URL

All API endpoints are relative to: `/accounts/api/`

## Endpoints

### Register User

Create a new user account.

- **URL**: `/register/`
- **Method**: `POST`
- **Auth Required**: No
- **Request Body**:
```json
{
    "email": "user@example.com",
    "full_name": "John Doe",
    "password": "securePassword123",
    "password2": "securePassword123"
}
```
- **Success Response**: `201 Created`
```json
{
    "user": {
        "id": "uuid",
        "email": "user@example.com",
        "full_name": "John Doe",
        "date_joined": "2025-01-01T12:00:00Z"
    },
    "refresh": "eyJ0eXAiOiJKV...",
    "access": "eyJ0eXAiOiJKV...",
    "message": "User registered successfully"
}
```

### Login (Get Tokens)

Authenticate a user and get access/refresh tokens.

- **URL**: `/token/`
- **Method**: `POST`
- **Auth Required**: No
- **Request Body**:
```json
{
    "email": "user@example.com",
    "password": "securePassword123"
}
```
- **Success Response**: `200 OK`
```json
{
    "refresh": "eyJ0eXAiOiJKV...",
    "access": "eyJ0eXAiOiJKV...",
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "date_joined": "2025-01-01T12:00:00Z"
}
```

### Refresh Token

Get a new access token using a refresh token.

- **URL**: `/token/refresh/`
- **Method**: `POST`
- **Auth Required**: No
- **Request Body**:
```json
{
    "refresh": "eyJ0eXAiOiJKV..."
}
```
- **Success Response**: `200 OK`
```json
{
    "access": "eyJ0eXAiOiJKV..."
}
```

### Logout

Blacklist a refresh token to log out a user.

- **URL**: `/logout/`
- **Method**: `POST`
- **Auth Required**: Yes (Bearer Token)
- **Request Body**:
```json
{
    "refresh": "eyJ0eXAiOiJKV..."
}
```
- **Success Response**: `200 OK`
```json
{
    "message": "Logout successful"
}
```

### Get User Info

Get the authenticated user's details.

- **URL**: `/user/`
- **Method**: `GET`
- **Auth Required**: Yes (Bearer Token)
- **Success Response**: `200 OK`
```json
{
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "date_joined": "2025-01-01T12:00:00Z"
}
```

### Update User Info

Update the authenticated user's details.

- **URL**: `/user/`
- **Method**: `PUT`
- **Auth Required**: Yes (Bearer Token)
- **Request Body**:
```json
{
    "full_name": "John Smith"
}
```
- **Success Response**: `200 OK`
```json
{
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Smith",
    "date_joined": "2025-01-01T12:00:00Z"
}
```

## Error Responses

The API uses standard HTTP status codes to indicate the success or failure of a request:

- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Missing or invalid authentication token
- `403 Forbidden`: The authenticated user doesn't have permission
- `404 Not Found`: The requested resource doesn't exist
- `500 Internal Server Error`: An unexpected error occurred

Error responses will include a JSON object with more details about the error.

## Authentication Headers

For protected endpoints, include the access token in the Authorization header:

```
Authorization: Bearer eyJ0eXAiOiJKV...
```

## Client Implementation Example

```javascript
// Example of a client implementation using the Fetch API

// Register a new user
async function registerUser(userData) {
  const response = await fetch('/accounts/api/register/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(userData)
  });
  return await response.json();
}

// Login and get tokens
async function login(email, password) {
  const response = await fetch('/accounts/api/token/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ email, password })
  });
  return await response.json();
}

// Refresh access token
async function refreshToken(refreshToken) {
  const response = await fetch('/accounts/api/token/refresh/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ refresh: refreshToken })
  });
  return await response.json();
}

// Protected API call example
async function getUserProfile(accessToken) {
  const response = await fetch('/accounts/api/user/', {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  });
  return await response.json();
}
```