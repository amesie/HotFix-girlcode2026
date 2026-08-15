# Verifi API

## Identity Checker

Checks a user's identifier against the Verifi synthetic demo dataset and
returns any identity integrity warning flags.

> **Security:** Verifi uses synthetic/demo identifiers only. It does not
> connect to real Home Affairs records.

### Endpoint

POST /api/check-identity

### Request

    {
      "idNumber": "DEMO-ID-001"
    }

### Successful response — clean record

    {
      "found": true,
      "idNumber": "DEMO-ID-001",
      "flags": [],
      "cleanRecord": true
    }

### Successful response — warning found

    {
      "found": true,
      "idNumber": "DEMO-ID-002",
      "flags": [
        {
          "type": "marital_status_mismatch",
          "severity": "high",
          "title": "Unexpected Marriage on Record",
          "plainExplanation": "The demo record shows a marriage that does not match the expected marital status.",
          "nextSteps": [
            "Verify the information with Home Affairs.",
            "Report suspected identity fraud to the appropriate authorities.",
            "Keep a record of your case or reference number."
          ]
        }
      ],
      "cleanRecord": false
    }

### Supported flag types

- marital_status_mismatch
- duplicate_id
- deceased_flag
- blocked_id
- no_flags

### Severity levels

- high
- medium
- low

### ID not found

    {
      "found": false,
      "idNumber": "DEMO-ID-999",
      "flags": [],
      "cleanRecord": false,
      "message": "No record found for this ID number in our demo dataset."
    }

### Error response

    {
      "error": true,
      "message": "Invalid ID number format"
    }

### Test Coverage

The Identity Checker currently tests:

- Clean records
- Fraudulent marriage
- Duplicate ID
- Deceased flag
- Blocked ID
- Unknown identifier

Current test result:

    6 passed

> All identifiers shown in this documentation are synthetic demo identifiers.
