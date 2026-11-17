 - Track: Tech Lead
 - Stake: Login and reset could break from XPath/DOM restyling. UX wanted profile fields on hosted
   Auth0 pages. A failed collect-before flow delayed registration. Every new customer account depends
   on this sequence.
 - Influence signal: Months to get a “no DOM” rule, then you refused UX’s registration page and
   proposed the sequence that shipped.
 - Context: UX needed Auth0 screens to match Jumbo branding beyond what Auth0 allows. The team
   composed HTML from a repo and restyled at load with DOM manipulation. Signup was also gated by
   three registration stacks (website, loyalty app, shopping app); the shopping app was end-of-life,
   so Auth0 signup stayed off until it left the stores. A colleague left with the Auth0 knowledge; you
   were asked to step in.
 - Action: You saw that UX kept asking for more, while XPath that Auth0 could change would break
   login/reset. You pushed TL and UX for months. Breakage and downgrades from broken scripts got
   management to agree. You removed the DOM layer and stayed on allowed Auth0 customization. For
   registration, UX wanted firstname on the Auth0 page; you said no. They designed collect-before;
   that team attempt failed without you (signup disabled, could not open the Auth0 signup page
   directly). You proposed collect-after Auth0. You worked frontend and Auth0 actions; it was not a
   solo build.
 - Result: No more runtime DOM on those pages. Every new customer is created by registering in Auth0
   first, then giving profile data after.
 - 60-second spoken version:
   “Auth0 login and reset were restyled with DOM and XPath on load. Those scripts broke or downgraded
   the pages when Auth0 changed markup. I pushed for months for a rule: no more DOM manipulation —
   only what Auth0 allows — and I removed that layer. Later UX wanted firstname on the Auth0
   registration page. I refused. They tried to collect data before Auth0; that failed without me,
   because signup was still disabled and we could not open the hosted page directly. I proposed we
   collect after Auth0 registration. That is how every new customer is created now.”
 - Words to use: pushed, rule, removed, refused, proposed, every new customer
 - Words to drop: we built (without splitting I), raised a concern, helped, led identity, inherited
   the whole Auth0 platform
 - Follow-ups they must be ready for:
     1. Did you ship the original DOM hacks?
     2. Why months if pages were already breaking?
     3. Collect-before failed without you — what did you own on the path that shipped?
     4. “Every new customer” — website only, or loyalty app too?
 - Gap: no break counts; final flow was team effort; shopping-app EOL was a gate, not your decision.

 Why this is next-level: You set a constraint others had to design around, then you sequenced the flow
 that became the default for new accounts.

 Dangerous follow-up: “Did you lead signup, or did you only say no and someone else built it?” Split:
 you owned the constraint and the collect-after decision; implementation was frontend + Auth0 actions
 with the team.