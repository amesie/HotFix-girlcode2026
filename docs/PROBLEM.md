# The Problem

Identity-related errors and fraud at Home Affairs are not abstract inconveniences — they can lock people out of everyday life, often without warning.

## Identity integrity

- **A fraudulently registered marriage** can be filed against someone's ID without their knowledge, affecting their legal and financial standing until it surfaces somewhere unexpected — a loan application, a tax filing, a dispute they didn't see coming.
- **A duplicate ID number**, linked to someone else's personal details, is a common early sign that an identity has been stolen or misused.
- **An incorrect deceased flag** can silently cut a living person off from banking, social grants, and other services that check ID status before granting access.
- **A blocked ID number** can prevent someone from accessing ID-dependent services with no visible explanation of why.

In every one of these cases, the person affected usually only finds out when something else fails — a bank account is frozen, a grant application is rejected — by which point the problem has already cost them time, money, or worse. There's no simple, plain-language way for someone to check "is anything wrong with my ID record?" before that happens.

## Process opacity

Separately, day-to-day Home Affairs processes — what documents a specific situation actually requires, what something costs, how long it takes, where to go — are not always easy to find in plain language when someone needs them. Requirements genuinely differ by situation (a first Smart ID application needs different documents than a lost-card replacement; a straightforward birth registration needs different documents than one involving an unmarried father or a deceased parent), so a single generic checklist is often wrong for a given person's actual case, and finding the right version of the information can mean a wasted trip to a branch.

## What Verifi does about it

Verifi addresses both halves of this directly:

1. **Identity Checker** surfaces identity-integrity problems — fraudulent marriage, duplicate ID, deceased flag, blocked ID — in language a non-expert can act on: what the flag means, and concrete next steps to resolve it, not a raw status code.
2. **Home Affairs Explained** answers the "what do I actually need" question for 4 common processes (birth registration, Smart ID, passport, name/surname amendment) by asking a few branching questions about the specific situation, then returning a document checklist tailored to that situation rather than a generic one — sourced from structured reference data, not guessed.

Verifi is a demo built on a synthetic dataset for the GirlCode Hackathon 2026 — it does not connect to real Home Affairs records. See the main [README](../README.md) for how it's built, and [SECURITY.md](SECURITY.md) for an honest account of what's actually implemented versus aspirational for a production version.
