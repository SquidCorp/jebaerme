- Track: Tech Lead
 - Stake: No gradual-release path. Staging would not prove the product. Platform did not want a POC in
   production. Marketing needed a real A/B.
 - Influence signal: You owned a production integration platform refused, unblocked infra, then the
   first marketing experiment ran on it.
 - Context: Your lead asked for a GrowthBook POC on the frontend platform. GrowthBook needed two ports
   (frontend + backend). Your infra did not allow a service to expose two ports.
 - Action: You took that to infra; they had to change the system to fit. You integrated GrowthBook
   client-side. Platform refused a POC in production. Your lead told you to solve it yourself; you
   found the person who could allow it. You owned maintaining the integration for the POC. Marketing
   then asked for the first A/B: a separate inspiration-newsletter checkbox at registration.
 - Result: You kept the split newsletter (you do not remember lift). GrowthBook stayed as the A/B
   framework and feature flags for gradual releases, which were not doable before.
 - 60-second spoken version:
   “I was asked to POC GrowthBook on our frontend. Infra could not deploy a service with two ports,
   which GrowthBook needed, so they had to change that. I got it into the frontend, but platform would
   not put a POC in production. I needed real traffic, not staging. My lead told me to solve that
   myself. I found the person who could allow it, and I owned the integration in production for the
   POC. Marketing ran our first A/B on it: a separate checkbox for the inspiration newsletter at
   registration. We kept the split. We also kept GrowthBook for feature flags and gradual releases. We
   could not do gradual releases before. I do not remember the lift number.”
 - Words to use: owned, unblocked, real traffic, found the person, kept, gradual releases
 - Words to drop: helped integrate, ran a POC (as the whole story), improved conversion, led the
   experimentation platform
 - Follow-ups they must be ready for:
     1. Who was the person who overrode platform’s no — role, not name?
     2. What did “own the integration” mean day to day (on-call, config, incidents)?
     3. Did other teams get GrowthBook, or only your frontend platform?
     4. Why no metric on the newsletter test?
 - Gap: unnamed counterpart; no lift; assigned POC, not a self-started strategy.

 Why this is next-level: You took production ownership nobody wanted, and you unblocked two other
 functions to get a real measurement.

 Dangerous follow-up: “Your lead assigned a POC. Where is the leadership?” Answer: platform said no,
 infra was blocked, you were told to solve it yourself, you put it on live traffic under your name,
 and it became the flag/A/B path.