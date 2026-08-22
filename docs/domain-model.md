## Domain Model

### Core Entities
```text
Client
Person
Employment
Requirement
Document
Classification
Review
Accountant Decision
```

### Relationships
```text
Client
 ├── has many Persons
 ├── has many Requirements
 └── has many Documents
```

```text
Person
 └── has many Employment records
```

```text
Employment
 └── contributes to document Requirements
```

```text
Document
 └── has Classification
```

```text
Document
 └── may require Review
```

```text
Requirement
 └── may have Accountant Decision
```

### Explanation:
```text
Employment = fact about the client
```

```text
Requirement = document we expect
```

```text
Document = file that actually arrived
```

```text
Classification = system's interpretation of that file
```

```text
Review = human intervention when automation is uncertain
```