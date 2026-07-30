/**
 * The backend returns Policyholder.identification_number,
 * InsuranceCompany.settlement_account_number, and Broker.bvn as full
 * plaintext (pgcrypto encryption is transparent at the ORM/API layer,
 * there is no server-side masking) -- this is a purely client-side
 * display convention applied consistently wherever these fields render.
 */
export function maskTail(value: string, visibleChars = 4): string {
  if (value.length <= visibleChars) return value;
  return `•••• ${value.slice(-visibleChars)}`;
}
