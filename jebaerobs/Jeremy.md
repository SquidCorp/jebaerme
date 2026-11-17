---
type: Person
name: Jérémy BAER
age: 37
nationality: French
city: Veghel
country: The Netherlands
relocating_to: Toulouse, France
relocating_when: 2027-06
skills:
  - "[[French]]"
  - "[[English]]"
  - "[[Dutch]]"
roles: []
education:
  - "[[education/Master degree|Master degree]]"
---

Add a real Role under `roles/` and put it in `roles:` above.

The Example notes are a shape demo only — do not link them here.


 1. Customers thought they had no account
 Backend said the API was fine. I traced account and order failures to a verified-email check on
 almost every navigation, plus three retries into Auth0’s Management API. That rate-limited us. I cut
 the client call. Checkout stopped looping; the fraud check stayed at partial coverage. Later we run
 it only after login.

 2. The chatbot is not the customer
 Security blocked a chatbot that wanted to borrow the shopper’s identity — 24-hour token, traces as
 the customer, access to every service. I said no. I designed OBO: agent identity, 5-minute token,
 traces as an agent, restricted scopes. I set up the Auth0 exchange; two other teams consume it. Beta,
 one use case, not the company default.

 3. GrowthBook on real traffic
 I got GrowthBook onto real traffic by owning a prod POC the platform team would not take. Infra had
 to allow a service to expose two ports. First experiment: a separate inspiration-newsletter checkbox
 at registration. We kept the split. We also got feature flags and gradual releases, which we could
 not do before. I do not remember the lift.

 4. No more DOM on Auth0
 Auth0 login and reset were restyled with DOM/XPath on load and those scripts broke pages. I pushed
 for months for “no more DOM — only what Auth0 allows,” and I removed that layer. UX wanted firstname
 on Auth0 registration; I refused. Collect-before failed without me. I proposed collect-after Auth0.
 That is how every new customer is created now.