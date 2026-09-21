# API

## Authentication
Create an API key under Settings → Developer. Send it in the `Authorization: Bearer <key>` header. Keys can be scoped to read-only or read-write.

## Rate limits
The API allows 100 requests per minute per key on Pro and 600 per minute on Team. When you exceed the limit you get HTTP 429 with a `Retry-After` header.

## Webhooks
Webhooks send a signed POST to your endpoint when events happen. Verify the `X-Signature` header with your webhook secret before trusting the payload. Failed deliveries are retried with exponential backoff for up to 24 hours.
