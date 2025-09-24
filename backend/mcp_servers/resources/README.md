# MCP Resources

This directory contains JSON resource files for the Model Context Protocol (MCP) servers.

## Resource Types

### Domain Resources

Domain resources provide knowledge about different speaking domains such as technical, corporate, and academic contexts.

Naming convention: `domain_<domain_id>.json`

Examples:
- `domain_technical.json`: Technical presentation guidelines
- `domain_corporate.json`: Corporate speaking guidelines
- `domain_academic.json`: Academic presentation guidelines

### User Resources

User resources contain user profiles, speaking history, and personalized improvement data.

Naming convention: `user_<user_id>.json`

Examples:
- `user_user123.json`: Profile for user "user123"
- `user_user456.json`: Profile for user "user456"

### Event Resources

Event resources provide knowledge about different speaking events such as presentations, interviews, and meetings.

Naming convention: `event_<event_id>.json`

Examples:
- `event_presentation.json`: Formal presentation guidelines
- `event_interview.json`: Job interview guidelines

### Audience Resources

Audience resources contain insights about different audience types such as technical, executive, and academic audiences.

Naming convention: `audience_<audience_id>.json`

Examples:
- `audience_technical.json`: Technical audience insights
- `audience_executive.json`: Executive audience insights
- `audience_academic.json`: Academic audience insights

## Resource URI Scheme

Resources in MCP are identified by URIs:

- Domain resources: `domain://<domain_id>`
- User resources: `user://<user_id>`
- Event resources: `event://<event_id>`
- Audience resources: `audience://<audience_id>`

## Adding New Resources

To add a new resource:

1. Create a JSON file following the naming convention
2. Follow the structure of existing resources of the same type
3. The MCP servers will automatically detect and make available the new resource

## Resource Templates

Resource templates allow for parameterized resource URIs. These are defined in each MCP server's implementation.
