"""Challenge Authoring Flow

A modular flow for creating challenges and bounties within a product context.
See full documentation in docs/challenge-and-bounty-posting-flow.md

Flow Steps:
1. Choose Challenge Type - Single/Multi skill and reward type
2. Describe Challenge - Title, description, and context
3. Specify Requirements - Add and configure bounties
4. Additional Information - Status, priority, and attachments
5. Review & Publish - Final validation and submission

Key Components:
- forms.py - Form definitions and validation
- services.py - Business logic and data handling
- views.py - View handling and flow control
- urls.py - URL routing

Templates:
    templates/product_management/flows/challenge_authoring/
    ├── main.html
    └── components/
        ├── step_1.html
        ├── step_2.html
        ├── step_3.html
        ├── step_4.html
        ├── step_5.html
        ├── step_nav.html
        ├── bounty_modal.html
        ├── skill_tree.html
        └── skill_tree_item.html

Static Files:
    static/js/flows/challenge_authoring/
    ├── main.js
    ├── bounty_modal.js
    ├── form_validation.js
    └── expertise_selector.js

    static/css/flows/challenge_authoring/
    └── bounty_modal.css

Usage:
    from product_management.flows.challenge_authoring.services import ChallengeAuthoringService
    
    service = ChallengeAuthoringService(request.user, product_slug)
    success, challenge, errors = service.create_challenge(challenge_data, bounties_data)

For full documentation and implementation details, see:
docs/challenge-and-bounty-posting-flow.md
"""
