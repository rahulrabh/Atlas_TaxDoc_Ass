## database

clients
   │
   └── tax_cases
          │
          ├── people
          │      │
          │      └── employments
          │
          ├── requirements
          │      │
          │      ├── requirement_decisions
          │      │
          │      └── requirement_document_matches
          │                    │
          │                    │
          └── documents ───────┘
                 │
                 ├── document_classifications
                 │
                 └── document_reviews

### clients - Represents the actual customer

clients
────────────────────────
id              UUID PK
name            VARCHAR
created_at      TIMESTAMP
updated_at      TIMESTAMP

### tax_cases - Represents one tax return for one client

tax_cases
────────────────────────
id              UUID PK
client_id       UUID FK → clients.id
tax_year        INTEGER
filing_status   VARCHAR
created_at      TIMESTAMP
updated_at      TIMESTAMP

- Relationship: Client 1 ─────── N TaxCases

### people - People participating in that tax case

people
────────────────────────
id              UUID PK
tax_case_id     UUID FK → tax_cases.id
name            VARCHAR
role            VARCHAR
created_at      TIMESTAMP
updated_at      TIMESTAMP

- Relationship: TaxCase 1 ─────── N People

### employments - Real-world employment facts

employments
────────────────────────
id              UUID PK
person_id       UUID FK → people.id
employer_name   VARCHAR
start_date      DATE
end_date        DATE NULL
created_at      TIMESTAMP
updated_at      TIMESTAMP

- Relationship: Person 1 ─────── N Employments

### requirements - This is the heart of the system

requirements
────────────────────────
id              UUID PK

tax_case_id     UUID FK → tax_cases.id
person_id       UUID FK → people.id NULL
employment_id   UUID FK → employments.id NULL

document_type   VARCHAR
tax_year        INTEGER

created_at      TIMESTAMP
updated_at      TIMESTAMP

- Examples: W-2
            person_id = Rahul
            employment_id = Company A
            document_type = W2
            tax_year = 2025

### documents - The actual uploaded files

documents
────────────────────────
id                  UUID PK
tax_case_id         UUID FK → tax_cases.id

file_name           VARCHAR
storage_key         VARCHAR
file_hash           VARCHAR UNIQUE

processing_status   VARCHAR

created_at          TIMESTAMP
updated_at          TIMESTAMP

### document_classifications - What the AI believes about a document

document_classifications
────────────────────────
id                  UUID PK
document_id         UUID FK → documents.id

document_type       VARCHAR
tax_year            INTEGER
person_id           UUID FK → people.id NULL
employment_id       UUID FK → employments.id NULL

confidence          DECIMAL

provider            VARCHAR
model               VARCHAR

created_at          TIMESTAMP

- Multiple classifications can exist for one document
    Document 1
        │
        ├── Classification 1
        ├── Classification 2
        └── Classification 3

### requirement_document_matches - Connects actual documents to expected requirements

requirement_document_matches
──────────────────────────────
id                  UUID PK

requirement_id      UUID FK → requirements.id
document_id         UUID FK → documents.id

match_status        VARCHAR
confidence          DECIMAL

created_at          TIMESTAMP
updated_at          TIMESTAMP

### requirement_decisions - Stores accountant decisions

requirement_decisions
────────────────────────
id                  UUID PK
requirement_id      UUID FK → requirements.id

decision            VARCHAR
reason              TEXT NULL

created_at          TIMESTAMP
created_by          UUID NULL

### document_reviews - Human review of uncertain documents

document_reviews
────────────────────────
id                  UUID PK
document_id         UUID FK → documents.id

reason              VARCHAR
status              VARCHAR
decision            VARCHAR NULL
notes               TEXT NULL

created_at          TIMESTAMP
reviewed_at         TIMESTAMP NULL