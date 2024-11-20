# platform

This is the platform that powers OpenUnited. [Apps](https://docs.djangoproject.com/en/4.2/ref/applications/) are used to create "bounded contexts" and logical separation between different parts of the platform:

Capabilities:

- Product Management (Product, Capability, Initiative, Challenge, Bounty etc.)
- Talent (Person, Skill, BountyClaim etc.)
- Commerce (Organisation, Points & Payments etc.)
- Engagement (Notifications etc.)

Other apps:

- Event Hub (Event Bus)
- Portal (UI for Management of Org, Products, Challenges, Bounties etc)
- Challenge Authoring Flow (UI and services for authoring challenges)

The apps aspire to be loosely coupled, and to use a service layer between views and models. This approach also allows us to use mocks to test the services effectively.

This repo contains the full platform including the frontend - which is deliberately simple.
We use a mix of TailwindCSS, DaisyUI and a mix of HTMX, AlpineJS and reluctantly JQuery where needed. Over time we may rewrite some things in ReactJS, but for now that's overkill and the focus is on evolving the platform to create value and getting mileage out of the most simple frontend tech possible. We initially started with a ReactJS frontend, but it just created bloat, difficulty in shipping features end-to-end and made it difficult to iterate on the platform efficientlyso we ditched it.


## Setting up The Project and Contributing

Please follow the instructions [here](.github/CONTRIBUTING.md).

## Getting Help

If you have any questions about OpenUnited:

- Ask a question on the OpenUnited Discord server. To invite yourself to the Discord server, visit https://discord.gg/T3xevYvWey.
- [File an issue.](https://github.com/OpenUnited/platform/issues)

Your feedback is always welcome.
