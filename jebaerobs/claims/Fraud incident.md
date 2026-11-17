
### Customers thought they had no account

 - Track: Tech Lead
 - Stake: Jumbo customers reporting they could not create an account or place an order. Timeouts, a
   spinning checkout, Auth0 Management API rate-limited. A fraud-related verified-email check was the
   sacred cow.
 - Influence signal: You persisted after backend dismissed it, cut the damaging call instead of adding
   people, then proved perceived outage vs actual failure.
 - Context: Customer-feedback Slack showed an unusual volume of “cannot create an account / cannot
   order.” Timeouts sat in front of your backend. Official incident process is P1/P2 only; this stayed
   a degraded service.
 - Action: You flagged the timeouts; backend said they had tested the API and it was not them. Days
   later, complaints continued. You stopped the place-order loop (redirect + “retry later” instead of
   spinning). You then traced it: client called “is this email verified?” on almost every navigation;
   that service hit Auth0 Management API every time; on failure it retried three times. You had
   backend drop retries as a hotfix, then you cut the client call — not the whole fraud feature.
   Manager did not want a full revert. You refused “add a colleague” and asked for room to remove the
   cause. Later you restored the check after login only. You ran an impact analysis afterward.
 - Result: Cutting the call recovered the flow immediately. Account creation was actually succeeding;
   bad unhappy-path UX made people think it had failed. Order impact was on incomplete profiles, not
   everyone. Same-week sales record is not your result.
 - 60-second spoken version:
   “Customers were saying they could not create an account or place an order. I saw backend timeouts.
   Backend said the API was fine. I still changed checkout so a timeout sent you back with a message
   instead of spinning forever. Then I traced it myself. The client was asking ‘is this email
   verified?’ on almost every navigation. That service called Auth0’s Management API every time, and
   retried three times on failure, so we rate-limited ourselves. I cut that client call. It recovered
   immediately. We kept partial fraud coverage, then later run the check only after login. Afterward I
   showed account creation was working — the UX made people think it had failed. It was never a P1. It
   was degraded service plus a bad error state.”
 - Words to use: traced, cut, stopped the loop, persisted, impact analysis, degraded
 - Words to drop: P1, owned the incident, reverted the feature, saved the sale, helped, just asked
   backend
 - Follow-ups they must be ready for:
     1. Why did this sit in Slack for days instead of a formal incident?
     2. Who shipped the every-navigation call — was it your feature?
     3. Why three retries and Management API on a hot path — did you miss that in review?
     4. Your manager wanted to keep the fraud feature. What exactly did you decide vs what TL/PO
        allowed?
 - Gap: no complaint counts; who introduced the call is unstated; not a declared incident owner on
   paper.

 Why this is next-level: You owned the customer outcome, not a ticket, and you cut scope under product
 pressure.

 Dangerous follow-up: “Was this your bug? If you are the Auth0/frontend reference, why did this design
 ship?” Answer with the design (every page + Management API + 3 retries), what you changed, and do not
 claim you ran major-incident command.