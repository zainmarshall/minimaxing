// Minimal auth utilities (placeholder)
import type { RequestEvent } from '@sveltejs/kit';

export function requireUser(event: RequestEvent) {
  // Placeholder: integrate with Supabase auth or real auth mechanism
  const user = (event.locals && (event.locals as any).user) || null;
  if (!user) throw new Error('Unauthorized');
  return user;
}

export async function getUser(event: RequestEvent) {
  return (event.locals && (event.locals as any).user) || null;
}
