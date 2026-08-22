# Domain Model

## Core Entities

Client
Person
Employment
Requirement
Document
Classification
Review
Accountant Decision

## Relationships

Client
 ├── has many Persons
 ├── has many Requirements
 └── has many Documents

Person
 └── has many Employment records

Employment
 └── contributes to document Requirements

Document
 └── has Classification

Document
 └── may require Review

Requirement
 └── may have Accountant Decision

### Explanation:

Employment = fact about the client
Requirement = document we expect
Document = file that actually arrived
Classification = system's interpretation of that file
Review = human intervention when automation is uncertain