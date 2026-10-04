import { URL } from "url";

// Allowed media providers & streaming CDN domains
const ALLOWED_DOMAIN_PATTERNS = [
    /streameeeeee\.site$/i,
    /vidstream/i,
    /rabbitstream/i,
    /megacloud/i,
    /streamwish/i,
    /filemoon/i,
    /hubcloud/i,
    /pixel\./i,
    /googleusercontent\.com$/i,
    /googleapis\.com$/i,
    /animedekho/i,
    /vidmoly/i,
    /turboviplay/i,
    /neocdn/i,
    /workers\.dev$/i,
    /cloudfront\.net$/i,
    /akamaized\.net$/i,
];

// Block internal / private IP addresses to prevent SSRF
const PRIVATE_IP_PATTERNS = [
    /^localhost$/i,
    /^127\./,
    /^0\./,
    /^10\./,
    /^192\.168\./,
    /^172\.(1[6-9]|2[0-9]|3[0-1])\./,
    /^169\.254\./,
    /^::1$/,
    /^fc00:/i,
    /^fe80:/i,
];

export function isValidProxyUrl(urlString: string): boolean {
    if (!urlString || typeof urlString !== "string") {
        return false;
    }

    try {
        const parsed = new URL(urlString);
        // Only allow HTTP/HTTPS
        if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
            return false;
        }

        const hostname = parsed.hostname.toLowerCase();

        // Check against private IP / localhost addresses
        for (const pattern of PRIVATE_IP_PATTERNS) {
            if (pattern.test(hostname)) {
                return false;
            }
        }

        // Must match an allowed streaming/media domain pattern
        const matchesAllowed = ALLOWED_DOMAIN_PATTERNS.some(pattern => pattern.test(hostname));
        return matchesAllowed;
    } catch {
        return false;
    }
}
