# platform

This is the platform that powers OpenUnited. [Apps](https://docs.djangoproject.com/en/4.2/ref/applications/) are used to create "bounded contexts" and logical separation between different parts of the platform:

Capabilities:

- Product Management (Product, Product Tree / Product Area, Initiative, Challenge, Bounty etc.)
- Talent (Person, Skill, BountyClaim etc.)
- Commerce (Organisation, Accounts,Points & Payments etc.)
- Engagement (Notifications etc.)
- Security (Role-based access control etc.)

Other apps:

- Event Hub (Event Bus)
- Portal (UI for Management of Org, Products, Challenges, Bounties etc)
- Challenge Authoring Flow (UI and services for authoring challenges)

The combination of being a marketplace of different personas and many new concepts and processes makes this a rather complex domain. The separation provided by apps is a simple mechanism to have boundaries without unnecessary complexity so we can predictably evolve the platform and create value rapidly.

The apps aspire to be loosely coupled, and we use a service layer between views and models. Services are also used to communicate across the boudaries of apps. This approach also allows us to use mocks to test the services effectively. Done is better than perfect, so you will find cases where this is (not yet) the case.

This repo contains the full platform including the frontend - which is deliberately simple. We use a mix of TailwindCSS, DaisyUI and a mix of HTMX, AlpineJS and reluctantly JQuery where it makes sense. We favour frontend simplicity and server-side rendering using django templates where possible. Over time we may rewrite some things in a fancier frontend stack or create mobile apps, but for now that's overkill and the focus is on evolving the platform to create value and getting mileage out of the most simple frontend tech possible to deliver excellent UX. The approach of having well-defined services, and thin views, makes evolving the frontend stack relatively simple.

## Setting up The Project and Contributing

Please follow the instructions [here](.github/CONTRIBUTING.md).

## Getting Help

If you have any questions about OpenUnited:

- Ask a question on the OpenUnited Discord server. To invite yourself to the Discord server, visit https://discord.gg/T3xevYvWey.
- [File an issue.](https://github.com/OpenUnited/platform/issues)

Your feedback is always welcome.
