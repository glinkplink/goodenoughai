# Decision record template

Copy this structure for new entries in [../DECISION_LOG.md](../DECISION_LOG.md).

---

## DEC-XXXX — Decision title

- **Status:** Proposed | Approved | Superseded | Rejected
- **Date:** YYYY-MM-DD
- **Context:**
  What situation or conflict required a decision? Link to issues, contradictions, or constraints.

- **Options considered:**
  1. Option A — brief description
  2. Option B — brief description
  3. Option C — brief description (if applicable)

- **Decision:**
  The chosen option. Be explicit and unambiguous.

- **Rationale:**
  Why this option best serves MVP goals, audience, cost, or trust requirements.

- **Consequences:**
  What must change in specs, implementation, timeline, or process as a result.

- **Revisit trigger:**
  Conditions under which this decision should be reconsidered.

- **Related documents:**
  - `docs/MVP_SCOPE.md` (or other affected spec)
  - `docs/ARCHITECTURE.md`

---

## Usage notes

- Assign next sequential ID (e.g., DEC-0011)
- Mark **Proposed** until explicit user or maintainer approval
- **Approved** decisions supersede conflicting planning material
- When superseding, update old entry status to **Superseded** with link to new DEC-ID
- Update [../MVP_SCOPE.md](../MVP_SCOPE.md), [../ARCHITECTURE.md](../ARCHITECTURE.md), or other affected specs when decision is approved
