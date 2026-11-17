- Track: Tech Lead
 - Stake: A customer-service chatbot was blocked by security. Their path was to borrow the shopper’s
   identity: 24-hour token, traces as the customer in Datadog, access to every service behind the
   gateway.
 - Influence signal: You said no under “go fast” pressure, set the token model, and split work across
   three teams.
 - Context: Website auth is a cookie; app auth is a JWT; the gateway checks it before routing. The
   chatbot team needed to call Jumbo services. You were asked for a quick workaround so they could
   ship.
 - Action: You refused impersonation. You designed OBO: agent has its own identity, 5-minute token,
   traces as an agent, restricted access. You set up Auth0 to expose token exchange. Integration team
   triggers and validates the OBO token. Chatbot team uses it to get a bounded customer. You did not
   build their bot.
 - Result: The pattern is in beta / limited, for this use case only. It is not the company default. Do
   not say you saved millions.
 - 60-second spoken version:
   “A team was ready to ship a customer-service chatbot and security blocked them on auth. They wanted
   to give the agent the customer’s identity — 24-hour token, traces as the shopper, access to any of
   our services. I said no. I designed on-behalf-of instead: the agent has its own identity, a
   five-minute token, traces as an agent, and only the services it needs. I set up Auth0 for the token
   exchange. Integration validates the token. The chatbot team consumes it. It’s in beta for that use
   case. It should become the default. It isn’t yet.”
 - Words to use: refused, said no, designed, set up Auth0 exchange, split the work, bounded, beta
 - Words to drop: helped, quick workaround we implemented, millions, rolled out to all agents, led the
   chatbot
 - Follow-ups they must be ready for:
     1. What scopes / which services are actually allowed?
     2. If OBO is standard elsewhere, what did you add vs copy from Auth0 docs?
     3. Who signed off — security, you, your lead?
     4. Why is it still one use case if you believe it should be the default?
 - Gap: exact scopes unstated; beta not general production; not an org standard.

 Why this is next-level: You used judgment without authority over that team, and you made the secure
 path the one they could ship.

 Dangerous follow-up: “Did you own this, or did you only click Auth0 config while they built the real
 system?” Answer with the split: you owned the identity model and the Auth0 exchange; you did not own
 the chatbot product.