import crypto from 'crypto';

export interface AdminSession {
  username: string;
  role: 'admin' | 'editor';
  createdAt: number;
}

const SESSION_SECRET = process.env.ADMIN_SESSION_SECRET || 'sps-cms-default-super-secure-secret-key-32chars!';

export function createSessionToken(username: string): string {
  const payload = JSON.stringify({
    username,
    role: 'admin',
    createdAt: Date.now()
  });
  const iv = crypto.randomBytes(16);
  const cipher = crypto.createCipheriv('aes-256-gcm', crypto.scryptSync(SESSION_SECRET, 'salt', 32), iv);
  let encrypted = cipher.update(payload, 'utf8', 'hex');
  encrypted += cipher.final('hex');
  const authTag = cipher.getAuthTag().toString('hex');
  return `${iv.toString('hex')}:${authTag}:${encrypted}`;
}

export function verifySessionToken(token: string): AdminSession | null {
  try {
    const [ivHex, authTagHex, encrypted] = token.split(':');
    if (!ivHex || !authTagHex || !encrypted) return null;

    const iv = Buffer.from(ivHex, 'hex');
    const authTag = Buffer.from(authTagHex, 'hex');
    const decipher = crypto.createDecipheriv('aes-256-gcm', crypto.scryptSync(SESSION_SECRET, 'salt', 32), iv);
    decipher.setAuthTag(authTag);

    let decrypted = decipher.update(encrypted, 'hex', 'utf8');
    decrypted += decipher.final('utf8');
    return JSON.parse(decrypted) as AdminSession;
  } catch {
    return null;
  }
}
