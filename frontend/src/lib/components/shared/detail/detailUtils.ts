import { marked } from 'marked';
import DOMPurify from 'dompurify';
// @ts-ignore
import { DateTime } from 'luxon';

/**
 * Render markdown to sanitized HTML
 */
export function renderMarkdown(markdown: string): string {
	if (!markdown) return '';
	return DOMPurify.sanitize(marked(markdown) as string);
}

/**
 * Render star rating as array of booleans
 */
export function renderStars(rating: number): boolean[] {
	const stars: boolean[] = [];
	for (let i = 1; i <= 5; i++) {
		stars.push(i <= rating);
	}
	return stars;
}

/**
 * Sort images by is_primary flag (primary images first)
 */
export function sortImagesByPrimary<T extends { is_primary?: boolean }>(images: T[]): T[] {
	return [...images].sort((a, b) => {
		if (a.is_primary && !b.is_primary) return -1;
		if (!a.is_primary && b.is_primary) return 1;
		return 0;
	});
}

/**
 * Sort visits by start_date chronologically (oldest first)
 */
export function sortVisitsChronologically<T extends { start_date?: string; created_at?: string }>(
	visits: T[]
): T[] {
	return [...visits].sort((a, b) => {
		const aTs = DateTime.fromISO(a.start_date || a.created_at || '').toMillis() || 0;
		const bTs = DateTime.fromISO(b.start_date || b.created_at || '').toMillis() || 0;
		return aTs - bTs;
	});
}

/**
 * Get local timezone
 */
export function getLocalTimezone(): string {
	return Intl.DateTimeFormat().resolvedOptions().timeZone ?? 'UTC';
}

/**
 * Get timezone label (use local if not provided)
 */
export function getTimezoneLabel(zone?: string | null): string {
	return zone ?? getLocalTimezone();
}

/**
 * Check if timezone differs from local
 */
export function shouldShowTimezoneBadge(zone?: string | null): boolean {
	return !!zone && getTimezoneLabel(zone) !== getLocalTimezone();
}

/**
 * Generate timezone tooltip text (pass translated strings)
 */
export function getTimezoneTip(
	zone: string | null | undefined,
	tripTzLabel: string = 'Trip TZ',
	yourTimeLabel: string = 'Your time'
): string | null {
	if (!zone) return null;
	const label = getTimezoneLabel(zone);
	const local = getLocalTimezone();
	if (label === local) return null;
	return `${tripTzLabel}: ${label}. ${yourTimeLabel}: ${local}.`;
}

/**
 * Format date in a specific timezone
 */
export function formatInTimezone(dateStr: string, timezone?: string | null): string {
	if (!dateStr) return '';
	const dt = DateTime.fromISO(dateStr, { zone: timezone ?? 'UTC' });
	if (!dt.isValid) return '';
	return dt.toLocaleString(DateTime.DATETIME_MED);
}

/**
 * Format date converted to local timezone
 */
export function formatToLocalTimezone(dateStr: string, sourceTimezone?: string | null): string {
	if (!dateStr) return '';
	const dt = DateTime.fromISO(dateStr, { zone: sourceTimezone ?? 'UTC' });
	if (!dt.isValid) return '';
	return dt.setZone(getLocalTimezone()).toLocaleString(DateTime.DATETIME_MED);
}
