# Zero-budget Google Cloud path

The All Things Agentic Hackathon offers a separate **$150 Google Cloud credit**
request for registered entrants. This is the preferred deployment path because it
keeps personal cash outlay at zero while producing real Cloud Run evidence.

Official resources:

- [Hackathon resources](https://allthingsagentichackathon.devpost.com/resources)
- [Credit request form](https://forms.gle/5PtXmw1dSbDnpYke9)
- [Hackathon FAQ](https://allthingsagentichackathon.devpost.com/details/faqs)

## Credit gate

- Request one code only; credits are first-come, first-served and not guaranteed.
- The form deadline is August 28, 2026 at 12:00 PM PT.
- The code must be redeemed before September 3, 2026.
- The $150 balance lasts 90 days after redemption.
- Do not deploy until the credit is visibly attached to the correct billing account.
- Credits cap the subsidy, not necessarily the account's total liability. Keep the
  service bounded and remove it after recording the required proof.

## Form answer

Track: **Fortified Enterprise Fleet**

> FleetShield helps community-relief coordinators safely run grant, medicine, and
> shelter agents without a dedicated reliability team. Three specialist Google ADK
> agents turn a witnessed side-effect failure into a deterministic, replay-tested,
> human-approved fleet control, with Gemini 3.5 and Cloud Run runtime evidence.

## Deployment controls

1. Use a dedicated FleetShield project.
2. Confirm the $150 promotional balance before enabling services.
3. Set minimum instances to zero and maximum instances to one.
4. Use request-based Cloud Run billing and 512 MiB memory.
5. Create budget alerts at $1, $10, and $100; alerts are not hard caps.
6. Do not add GPUs, paid Marketplace services, domains, or minimum instances.
7. Record the `.run.app` URL, Cloud Run revision, Gemini/ADK policy source, and
   `/api/evidence` output in the four-minute video.
8. After recording, disable public access or delete the service while keeping the
   video, repository, and logs required by the rules.

GEAR's 35 monthly credits are for Google Skills labs. They are useful for training,
but they are not the same as the hackathon's deployable Google Cloud credit.
