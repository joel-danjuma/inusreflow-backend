/** Curated policy-type suggestions -- policy_type stays an open string on
 * the backend (no CHECK constraint, no enum), so this list only shapes the
 * UI: consistent values going forward for filtering, while "Other" still
 * accepts free text for anything not covered here. */
export const CURATED_POLICY_TYPES = [
  "AUTO",
  "HEALTH",
  "LIFE",
  "PROPERTY",
  "MARINE",
  "TRAVEL",
  "BUSINESS",
  "HOME",
] as const;

export type CuratedPolicyType = (typeof CURATED_POLICY_TYPES)[number];

export const POLICY_TYPE_LABELS: Record<CuratedPolicyType, string> = {
  AUTO: "Auto",
  HEALTH: "Health",
  LIFE: "Life",
  PROPERTY: "Property",
  MARINE: "Marine",
  TRAVEL: "Travel",
  BUSINESS: "Business",
  HOME: "Home",
};
