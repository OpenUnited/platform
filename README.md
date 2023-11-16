# platform

This is the platform that powers OpenUnited. [Apps](https://docs.djangoproject.com/en/4.2/ref/applications/) are used to create "bounded contexts":

- Product Management (Product, Capability, Initiative, Challenge, Bounty etc.)
- Talent (Person, Skill, BountyClaim etc.)
- Commerce (Organisation, Points & Payments etc.)
- Engagement (Notifications etc.)

Each app has a services.py file that implements the "public" services interface for that app/bounded context.

This repo contains the full platform including the frontend - which is "deliberately simple"*. We prototype and specify the target UX, as code, in the [UX Prototype repo](https://github.com/OpenUnited/ux-prototype). The UX Prototype repo is not for production use, we use it instead of using Figma.

\* Our "deliberately simple" frontend means that we use [Jinja](https://jinja.palletsprojects.com/en/3.1.x/) templates, [TailwindCSS](https://tailwindcss.com/), [TailwindUI](https://tailwindui.com/), [Hyperscript](https://hyperscript.org/), plain javascript where needed, and [HTMX](https://htmx.org/) where it improves the UX. Earlier we had a separate ReactJS frontend and a GraphQL API layer, however [such fanciness](https://www.youtube.com/watch?v=Uo3cL4nrGOk) failed to deliver the expected value, whilst creating complexity/friction... therefore, we now have a deliberately simple frontend. As a result, we have about 50% less code and move way faster. 

## Setting up The Project and Contributing

Please follow the instructions [here](.github/CONTRIBUTING.md).

## Getting Help

If you have any questions about OpenUnited:

- Ask a question on the OpenUnited Discord server. To invite yourself to the Discord server, visit https://discord.gg/T3xevYvWey.
- [File an issue.](https://github.com/OpenUnited/platform/issues)

Your feedback is always welcome.
