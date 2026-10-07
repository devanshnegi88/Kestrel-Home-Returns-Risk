# Operational decision framework

## Score bands

**Standard flow**

Risk score below the policy call break-even benchmark. No special action from the model; continue normal fulfilment.

**Call candidate**

Risk score at/above 11.18% and below the 50% review threshold. Prioritize a confirmation call. The policy says the pilot prevented about 35% of otherwise-occurring returns on called orders.

**High risk**

Risk score at/above 50%. Send to manual review before dispatch. This is a review trigger, not permission to cancel the order automatically.

## Why two thresholds?

The 11.18% threshold is derived from policy economics. The 50% threshold is an intentionally conservative review queue for the highest-risk tail. The model does not have enough evidence to justify a hard dispatch hold threshold.

## What the operator should do

1. Review the returned reasons shown by the application.
2. For call candidates, confirm model, address, delivery expectations, and buyer intent.
3. Log call disposition.
4. Do not silently override the model; record an operational reason.
5. Feed outcomes back into the next training cycle.
