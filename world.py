"""A synthetic fiat-to-crypto on-ramp, March to September 2026.

40 wallet partners send buy sessions. On 2026-05-14 four launch partners turn on a headless
checkout: Apple Pay embedded in the partner's own app, no redirect, no re-authentication for
verified users, an inline onboarding frame for new ones. Ten more partners follow on 2026-07-01,
ten on 2026-08-15, and sixteen never do.

The traps are the ones a product data team hits on this kind of launch:
  - headless traffic is iOS by construction and, at first, mostly returning verified users
  - the launch partners were picked because they were growing, and a market rally lifts every
    partner's intent from May to July
  - card issuers decide a large share of outcomes: some banks block crypto purchases outright,
    and the mix of banks differs by partner region
  - chargebacks arrive weeks to months after the purchase

Every headless session is also scored under the old widget with the same random draws, so the
true effect of the launch is known per session. Fixed seed. No real partner, user or bank.
"""
import math
import random

SEED = 30_000_000          # customers, per the company's own count
DAYS = 214                 # day 0 = 2026-03-01, day 213 = 2026-09-30
WAVES = {74: 4, 122: 10, 167: 10}   # 2026-05-14, 2026-07-01, 2026-08-15
N_PARTNERS = 40
REGIONS = {"US": 0.40, "EEA": 0.30, "UK": 0.15, "ROW": 0.15}
# share of a region's cards issued by banks that block crypto / are cautious / are friendly
ISSUER_MIX = {"US": (0.10, 0.30, 0.60), "EEA": (0.12, 0.35, 0.53),
              "UK": (0.38, 0.34, 0.28), "ROW": (0.20, 0.40, 0.40)}
DECLINE = {"blocks": 0.70, "cautious": 0.28, "friendly": 0.07}
APPLE_PAY_DECLINE_X = 0.85         # tokenized credential, same issuer policy
KYC_PASS, KYC_MAX = 0.67, 3        # ~1.5 attempts per pass, $1 each
# probability a session clears the checkout step (redirect, re-auth or inline frame)
CLEAR = {("widget", True): 0.78, ("widget", False): 0.70,
         ("headless", True): 0.93, ("headless", False): 0.76}
QUOTE = {True: 0.62, False: 0.40}  # returning / new: proceeds past the quote screen
FRAUD = {True: 0.003, False: 0.012}
APPLE_PAY_FRAUD_X = 0.45


def rally(d):
    """market intent bump, peaks late May, gone by mid July"""
    return math.exp(-((d - 95) / 22) ** 2)


def partners(rng):
    ps = []
    for i in range(N_PARTNERS):
        region = rng.choices(list(REGIONS), weights=list(REGIONS.values()))[0]
        ps.append(dict(pid=i, region=region, weight=rng.lognormvariate(0, 0.7),
                       ios=rng.uniform(0.30, 0.70), ret=rng.uniform(0.35, 0.55), growth=0.0, launch=None))
    # launch partners: the biggest iOS-heavy ones that were already growing their engaged base
    order = sorted(ps, key=lambda p: -p["weight"] * p["ios"])
    for p in order[:4]:
        p["ios"] = max(p["ios"], 0.72)
        p["growth"] = 0.0016
    rest = order[4:]
    rng.shuffle(rest)
    k = 0
    for day, n in WAVES.items():
        group = order[:4] if day == 74 else rest[k:k + n]
        if day != 74:
            k += n
        for p in group:
            p["launch"] = day
    return ps


def session(rng, p, d):
    ret = rng.random() < min(0.85, p["ret"] + p["growth"] * d)
    ios = rng.random() < p["ios"]
    headless = p["launch"] is not None and d >= p["launch"] and ios
    u_quote, u_clear, u_pm, u_iss, u_dec, u_fraud = (rng.random() for _ in range(6))
    intent = 1 + 0.30 * rally(d)
    quoted = u_quote < min(0.95, QUOTE[ret] * intent)
    kyc_attempts, kyc_ok = 0, True
    if quoted and not ret:
        kyc_ok = False
        for _ in range(KYC_MAX):
            kyc_attempts += 1
            if rng.random() < KYC_PASS:
                kyc_ok = True
                break
            if rng.random() < 0.35:
                break
    mix = ISSUER_MIX[p["region"]]
    issuer = "blocks" if u_iss < mix[0] else ("cautious" if u_iss < mix[0] + mix[1] else "friendly")
    amount = round(rng.lognormvariate(math.log(150), 0.9), 2)
    lag = int(rng.lognormvariate(math.log(45), 0.5))

    def outcome(path):
        if not (quoted and kyc_ok):
            return dict(cleared=False, auth=False, done=False, apple=False)
        cleared = u_clear < CLEAR[(path, ret)]
        apple = path == "headless" or (ios and u_pm < 0.35)
        if not cleared:
            return dict(cleared=False, auth=False, done=False, apple=apple)
        declined = u_dec < DECLINE[issuer] * (APPLE_PAY_DECLINE_X if apple else 1)
        return dict(cleared=True, auth=True, done=not declined, apple=apple)

    real = outcome("headless" if headless else "widget")
    cf = outcome("widget")
    fraud = real["done"] and u_fraud < FRAUD[ret] * (APPLE_PAY_FRAUD_X if real["apple"] else 1)
    return dict(day=d, pid=p["pid"], region=p["region"], ret=ret, ios=ios, headless=headless,
                quoted=quoted, kyc_attempts=kyc_attempts, issuer=issuer, apple=real["apple"],
                reached_auth=real["auth"], done=real["done"], cf_done=cf["done"],
                amount=amount, fraud=fraud, cb_day=d + lag if fraud else None)


def build():
    rng = random.Random(SEED)
    ps = partners(rng)
    rows = []
    for d in range(DAYS):
        vol = 1 + 0.35 * rally(d)
        for p in ps:
            n = int(rng.gauss(46 * p["weight"] * vol, 4) + 0.5)
            for _ in range(max(0, n)):
                rows.append(session(rng, p, d))
    return ps, rows


if __name__ == "__main__":
    ps, rows = build()
    print(len(rows), "sessions,", sum(r["done"] for r in rows), "purchases")
