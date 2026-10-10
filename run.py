"""python3 run.py  -- stdlib only, a few seconds.

Did the headless checkout lift conversion, and how would a product data team know?
Four readings of the same launch, scored against the true effect (every headless session is also
played out under the old widget with the same random draws). Then where partner conversion gaps
come from, and what the launch's chargeback rate looks like before it matures.
"""
import time
from collections import defaultdict

import world as W

T0 = time.time()
ps, rows = W.build()
P = {p["pid"]: p for p in ps}
AS_OF = W.DAYS - 1


def rate(rs, key="done"):
    return sum(r[key] for r in rs) / max(1, len(rs))


print("=" * 92)
print("Did the headless checkout lift conversion? A synthetic on-ramp, Mar-Sep 2026")
print("=" * 92)
print(f"{len(ps)} partners, {len(rows):,} buy sessions, {sum(r['done'] for r in rows):,} purchases. "
      f"Headless launches: 4 partners 2026-05-14, 10 on 07-01, 10 on 08-15, 16 never.")

# ---- 1. four readings of the launch effect --------------------------------------------------
treated = [r for r in rows if r["headless"]]
true_lift = (sum(r["done"] for r in treated) - sum(r["cf_done"] for r in treated)) / len(treated)
true_rel = true_lift / rate(treated, "cf_done")

# a) headless vs widget sessions after launch, at partners that have it
on = [r for r in rows if P[r["pid"]]["launch"] is not None and r["day"] >= P[r["pid"]]["launch"]]
a = rate([r for r in on if r["headless"]]) - rate([r for r in on if not r["headless"]])

# b) launch partners, 6 weeks before vs 6 weeks after 05-14 (all their sessions, as a dashboard would)
L = 74
launch_p = {p["pid"] for p in ps if p["launch"] == L}
pre = [r for r in rows if r["pid"] in launch_p and L - 42 <= r["day"] < L]
post = [r for r in rows if r["pid"] in launch_p and L <= r["day"] < L + 42]
b_all = rate(post) - rate(pre)
b_ios = rate([r for r in post if r["ios"]]) - rate([r for r in pre if r["ios"]])


# c) stacked diff-in-diff: each wave vs partners not yet treated, iOS sessions, 4 weeks each side
def did(seg=None):
    num = den = 0.0
    for day in W.WAVES:
        tr = {p["pid"] for p in ps if p["launch"] == day}
        ctl = {p["pid"] for p in ps if p["launch"] is None or p["launch"] > day + 28}

        def cell(group, lo, hi):
            rs = [r for r in rows if r["pid"] in group and lo <= r["day"] < hi and r["ios"]]
            if seg is not None:
                rs = [r for r in rs if r["ret"] == seg]
            return rs

        t0, t1 = cell(tr, day - 28, day), cell(tr, day, day + 28)
        c0, c1 = cell(ctl, day - 28, day), cell(ctl, day, day + 28)
        est = (rate(t1) - rate(t0)) - (rate(c1) - rate(c0))
        num += est * len(t1)
        den += len(t1)
    return num / den


c = did()
# d) same, within returning / new, re-weighted to the treated sessions' mix
share_ret = sum(r["ret"] for r in treated) / len(treated)
d = share_ret * did(True) + (1 - share_ret) * did(False)

print("\n1. THE LAUNCH EFFECT, FOUR WAYS (conversion = purchases / buy sessions, percentage points)")
print(f"   {'reading':<62}{'estimate':>10}{'vs truth':>11}")
for name, v in [("headless vs widget sessions, same partners, after launch", a),
                ("launch partners, 6 weeks after vs 6 weeks before (all sessions)", b_all),
                ("   same, iOS sessions only", b_ios),
                ("diff-in-diff vs not-yet-launched partners, iOS sessions", c),
                ("   same, within returning / new users, re-weighted", d)]:
    print(f"   {name:<62}{v * 100:>+9.1f}{v / true_lift:>10.1f}x")
print(f"   {'TRUE effect on headless sessions (same draws, old widget)':<62}{true_lift * 100:>+9.1f}"
      f"      ({true_rel:+.0%} relative)")
inc = sum(r["done"] for r in treated) - sum(r["cf_done"] for r in treated)
inc_usd = sum(r["amount"] for r in treated if r["done"] and not r["cf_done"])
print(f"   = {inc:,} purchases the launch actually caused, ${inc_usd / 1e6:.2f}M of volume, "
      f"out of {sum(r['done'] for r in treated):,} headless purchases")
ret_head = sum(r["ret"] for r in treated) / len(treated)
ret_wid = sum(r["ret"] for r in on if not r["headless"]) / max(1, sum(not r["headless"] for r in on))
print(f"   why (a) is wrong: headless sessions are {ret_head:.0%} returning users vs {ret_wid:.0%} on the widget, "
      f"and all iOS")

# ---- 2. where partner conversion gaps come from ----------------------------------------------
print("\n2. WHY PARTNERS CONVERT DIFFERENTLY: checkout vs the card issuer")
by = defaultdict(list)
for r in rows:
    if r["day"] < L:                       # before any launch, so the checkout is identical
        by[r["pid"]].append(r)
stats = []
for pid, rs in by.items():
    q = [r for r in rs if r["reached_auth"]]
    stats.append(dict(pid=pid, region=P[pid]["region"], conv=rate(rs), to_auth=rate(rs, "reached_auth"),
                      approve=rate(q) if q else 0, n=len(rs)))
stats.sort(key=lambda s: s["conv"])
worst = stats[:10]
by_auth = sorted(stats, key=lambda s: s["to_auth"])[:10]
overlap = len({s["pid"] for s in worst} & {s["pid"] for s in by_auth})
print(f"   pre-launch (Mar 1 - May 13), when every partner had the same widget:")
print(f"   conversion ranges {stats[0]['conv']:.1%} to {stats[-1]['conv']:.1%} across partners")
import statistics as S
var_conv = S.pvariance([s["conv"] for s in stats])
# conv = to_auth * approve; share of variance that the approval rate alone explains
mean_auth = S.mean(s["to_auth"] for s in stats)
var_from_issuer = S.pvariance([mean_auth * s["approve"] for s in stats])
print(f"   holding the funnel before payment at its average, issuer approval alone reproduces "
      f"{var_from_issuer / var_conv:.0%} of the variance in partner conversion")
regions = defaultdict(int)
for s in worst:
    regions[s["region"]] += 1
print(f"   the 10 lowest-converting partners: {dict(regions)} by region; only {overlap} of them are also in "
      f"the bottom 10 for reaching payment")
print(f"   approval rate after a cleared checkout, by partner region:")
for reg in W.REGIONS:
    rs = [r for r in rows if r["region"] == reg and r["reached_auth"] and r["day"] < L]
    print(f"      {reg:<4} {rate(rs):.1%}   ({sum(r['issuer'] == 'blocks' for r in rs) / len(rs):.0%} of cards from "
          f"banks that block crypto)")

# ---- 3. the chargeback rate before it matures -------------------------------------------------
print("\n3. HEADLESS FRAUD, READ ON 2026-09-30 vs WHEN MATURE (chargebacks per 1,000 purchases)")
print(f"   {'purchase month':<16}{'path':<10}{'purchases':>10}{'seen by 09-30':>15}{'eventual':>10}{'seen share':>12}")
months = [("May 14-31", 74, 92), ("June", 92, 122), ("July", 122, 153), ("August", 153, 184), ("September", 184, 214)]
for label, lo, hi in months:
    for path in (True, False):
        rs = [r for r in rows if r["done"] and lo <= r["day"] < hi and r["headless"] == path and r["ios"]]
        seen = sum(1 for r in rs if r["fraud"] and r["cb_day"] <= AS_OF)
        ever = sum(r["fraud"] for r in rs)
        print(f"   {label:<16}{'headless' if path else 'widget':<10}{len(rs):>10,}{seen / len(rs) * 1000:>15.2f}"
              f"{ever / len(rs) * 1000:>10.2f}{(seen / ever if ever else 0):>11.0%}")

recent = [r for r in rows if r["done"] and r["day"] >= 153 and r["ios"]]
early = lambda path: sum(1 for r in recent if r["headless"] == path and r["fraud"] and r["cb_day"] <= AS_OF) / \
    max(1, sum(1 for r in recent if r["headless"] == path))
ever = lambda path: sum(1 for r in recent if r["headless"] == path and r["fraud"]) / \
    max(1, sum(1 for r in recent if r["headless"] == path))
print(f"   Aug-Sep iOS purchases: headless looks {early(True) * 1000:.2f} vs widget {early(False) * 1000:.2f} per 1,000 today;"
      f" mature it's {ever(True) * 1000:.2f} vs {ever(False) * 1000:.2f}")

kyc = sum(r["kyc_attempts"] for r in rows)
print(f"\nKYC: {kyc:,} attempts at $1 each, {kyc / max(1, sum(1 for r in rows if r['kyc_attempts'])):.2f} per new user who started")
print(f"ran in {time.time() - T0:.1f}s")
