// Throwaway-inbox domains the free checklist won't go to (11-25, Elijah's abuse layers: Gmail normalization + this list + one free per
// device + a soft per-IP limit; no fingerprinting, no SMS, some leakage accepted). Matches the domain and any subdomain of it.
// Add to it when a new one shows up in the users table; it never blocks paid checkouts of people already signed in.
export const DISPOSABLE = new Set([
  '10minutemail.com', '10minutemail.net', '20minutemail.com', '33mail.com', 'anonaddy.me', 'burnermail.io', 'byom.de', 'mailtemp.net',
  'discard.email', 'dispostable.com', 'dropmail.me', 'emailondeck.com', 'emailtemporanea.com', 'fakeinbox.com', 'fakemail.net',
  'getairmail.com', 'getnada.com', 'guerrillamail.biz', 'guerrillamail.com', 'guerrillamail.de', 'guerrillamail.info', 'guerrillamail.net',
  'guerrillamail.org', 'guerrillamailblock.com', 'harakirimail.com', 'inboxbear.com', 'inboxkitten.com', 'incognitomail.org', 'mail.tm',
  'mail-temp.com', 'mailcatch.com', 'maildrop.cc', 'mailinator.com', 'mailinator.net', 'mailinator2.com', 'mailnesia.com', 'mailnull.com',
  'mailpoof.com', 'mailsac.com', 'mintemail.com', 'moakt.com', 'mohmal.com', 'mytemp.email', 'nada.email', 'sharklasers.com',
  'spam4.me', 'spamgourmet.com', 'spambox.us', 'temp-mail.io', 'temp-mail.org', 'tempail.com', 'tempinbox.com', 'tempmail.com',
  'tempmail.dev', 'tempmail.net', 'tempmailo.com', 'tempr.email', 'throwawaymail.com', 'trashmail.com', 'trashmail.de', 'trashmail.net',
  'yopmail.com', 'yopmail.fr', 'yopmail.net', 'emailfake.com', 'luxusmail.org', 'tmail.ws', 'tmpmail.org', 'tmpmail.net', 'linshiyouxiang.net',
  'grr.la', 'pokemail.net', 'spamthisplease.com', 'wegwerfmail.de', 'einrot.com', 'cuvox.de', 'dayrep.com', 'fleckens.hu', 'gustr.com',
  'jourrapide.com', 'rhyta.com', 'superrito.com', 'teleworm.us', 'armyspy.com', 'mailforspam.com', 'tempmailaddress.com', 'mvrht.net',
  'mailbox.in.ua', 'minuteinbox.com', 'emltmp.com', 'trbvm.com', 'ezztt.com', 'vomoto.com', 'xojxe.com', 'yomail.info',
]);

export function disposable(domain) {
  const parts = String(domain || '').toLowerCase().split('.');
  for (let i = 0; i < parts.length - 1; i++) if (DISPOSABLE.has(parts.slice(i).join('.'))) return true;
  return false;
}
