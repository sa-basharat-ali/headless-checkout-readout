# Did the headless checkout move conversion?

```
python3 run.py      # stdlib only, about 4 seconds
```

A synthetic fiat-to-crypto on-ramp, March to September 2026: 40 wallet partners, 458,119 buy
sessions, 136,856 purchases. On May 14 four launch partners turn on a headless checkout (Apple Pay
embedded in the partner's app, no redirect, no re-authentication for verified users). Ten more
follow on July 1, ten on August 15, sixteen never do.

Every headless session is also played out under the old widget with the same random draws, so the
true effect of the launch is known exactly: **+6.1 points of conversion (+20% relative), 4,578
purchases and $1.04M of volume the launch actually caused**, out of 27,749 headless purchases.
Fixed seed, no real partner, user or bank.

## 1. Four readings of the same launch

| reading | estimate | vs truth |
|---|---|---|
| headless vs widget sessions, same partners, after launch | +8.8 pts | 1.4x |
| launch partners, 6 weeks after vs 6 weeks before | +13.2 pts | 2.2x |
| same, iOS sessions only | +15.2 pts | 2.5x |
| diff-in-diff vs partners not yet launched, iOS sessions | +7.0 pts | 1.1x |
| same, within returning and new users | +6.7 pts | 1.1x |
| **true effect** | **+6.1 pts** | |

The before/after read is the one a launch dashboard shows, and it is off by 2.2x. The launch
landed in a market rally: partners that hadn't launched yet gained 6.3 points over the same four
weeks. Headless sessions are also all iOS and more often returning verified users (58% vs 51%),
so comparing them with widget sessions credits the checkout with who the users already were.

Diff-in-diff against partners that hadn't launched yet gets close. Split by user type it lands
within about a point of the truth on every wave (returning users +10.5 vs +10.6 true on the May
wave), and the effect is about four times larger for returning users than for new ones, who
still go through onboarding.

## 2. Partner conversion gaps are mostly the card issuer

Before any launch, with the same widget everywhere, partner conversion ranged from 21.0% to 31.5%.
Issuer approval alone reproduces **75% of that variance**. Six of the ten lowest-converting
partners are UK-heavy, where 38% of cards come from banks that block crypto purchases and approval
after a cleared checkout is 62.6% (US: 81.2%). Only 4 of the bottom 10 are also bottom 10 for
reaching the payment step, so a ranking on end-to-end conversion sends the product team to fix
checkouts that work.

## 3. Headless fraud looks better than it is, for now

Chargebacks arrive weeks to months after the purchase (median 45 days here). Read on September 30,
August and September iOS purchases show **0.27 chargebacks per 1,000 on headless vs 1.15 on the
widget**. Once they mature it's 1.71 vs 4.62. Headless is safer, because Apple Pay is, but the early
read puts the gap at 4.3x instead of 2.7x, and understates headless's own rate about sixfold,
because most headless volume is recent.

## What surprised me

I expected re-weighting by user type to fix the pooled diff-in-diff. It barely moved it (7.0 to
6.7). Per wave and per user type the method was already right. The leftover error came from mixing
returning and new users, whose conversion responds differently to the rally, across windows where
their shares were shifting. So the fix is to report the effect by user type, not to apply a better
correction to the total.

## Files

| | |
|---|---|
| `world.py` | partners, rollout waves, rally, issuers, KYC, chargeback lag, counterfactual per session |
| `run.py` | the four readings, the issuer decomposition, chargeback maturity |
| `index.html` | the write-up as a page |

Syed Ahmed Basharat Ali · basharat.net
