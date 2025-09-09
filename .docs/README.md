# Documentation & Version Management

This directory contains project documentation and version management files for the SaaSControlDeck platform.

## Structure

```
.docs/
├── README.md                 # This file
├── versions/                 # Version management directory
│   ├── v1.0.0/              # Version-specific documentation
│   │   ├── CHANGELOG.md     # Changes in this version
│   │   ├── RELEASE_NOTES.md # Release notes
│   │   ├── MIGRATION.md     # Migration guide
│   │   └── docs/            # Version-specific docs
│   └── latest/              # Symlink to latest version
├── architecture/            # System architecture docs
├── api/                     # API documentation
└── deployment/              # Deployment guides
```

## Version Management Guidelines

- Each version gets its own directory under `versions/`
- Version directories follow semantic versioning (e.g., v1.0.0, v1.1.0, v2.0.0)
- The `latest/` directory always points to the most recent version
- Critical files for each version:
  - `CHANGELOG.md`: Detailed changes
  - `RELEASE_NOTES.md`: User-facing notes
  - `MIGRATION.md`: Upgrade instructions (if needed)

## Documentation Types

- **Architecture**: System design and technical architecture
- **API**: REST API documentation and examples
- **Deployment**: Installation and deployment guides
- **User Guides**: End-user documentation
- **Developer Guides**: Development setup and contribution guides