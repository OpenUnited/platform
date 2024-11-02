"""Challenge Authoring Flow

A modular flow for creating challenges and bounties within a product context.
See full documentation in docs/challenge-and-bounty-posting-flow.md

Flow Steps:
1. Choose Challenge Type - Single/Multi skill and reward type
2. Describe Challenge - Title, description, and context
3. Specify Requirements - Add and configure bounties
4. Additional Information - Status, priority, and attachments
5. Review & Publish - Final validation and submission

Security:
- Integrated with RoleService for permission management
- Requires Product Manager or Admin role
- Multi-level permission validation
- Transaction-level security checks

Directory Structure:
├── __init__.py
├── forms.py
├── services.py
├── views.py
├── urls.py
├── docs/
│   └── flow.md
├── partials/
│   └── expertise_options.html  # Server-side expertise selection template
├── templates/
│   ├── main.html
│   └── components/
│       ├── step_1.html
│       ├── step_2.html
│       ├── step_3.html
│       ├── step_4.html
│       ├── step_5.html
│       ├── step_nav.html
│       ├── bounty_modal.html
│       ├── bounty_table.html
│       ├── form_buttons.html
│       ├── navigation.html
│       ├── skill_tree.html
│       └── skill_tree_item.html
└── static/
    ├── js/
    │   ├── main.js
    │   ├── bounty_modal.js
    │   └── form_validation.js
    └── css/
        └── bounty_modal.css

Business Rules:
- Title length: 10-200 characters
- Description length: 50-5000 characters
- Points range: 1-1000 per bounty
- Maximum 10 bounties per challenge

Usage:
    from product_management.flows.challenge_authoring.services import ChallengeAuthoringService
    
    service = ChallengeAuthoringService(request.user, product_slug)
    success, challenge, errors = service.create_challenge(challenge_data, bounties_data)

For full documentation and implementation details, see:
docs/challenge-and-bounty-posting-flow.md
"""
