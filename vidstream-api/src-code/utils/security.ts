import { URL } from "url";

// V2 #6 + V2 #22: STRICT hostname allowlist — suffix-anchored only.
// Bare substring matches (e.g. /vidstream/i matching "evilvidstream.com")
// are forbidden. Every entry requires either an exact host or a
// ".domain.tld" suffix so attacker-controlled lookalikes are rejected.
const ALLOWED_EXACT_HOSTS = new Set([
    "streameeeeee.site",
    "animedekho.tv",
    "animedekho.app",
    "drive.toonflix.in",
    "files.toonflix.in",
    "toonflix.in",
]);

// Suffixes: host must equal the suffix or end with "." + suffix.
const ALLOWED_SUFFIXES = [
    "streameeeeee.site",
    "vidstream.to",
    "vidstream.cc",
    "rabbitstream.net",
    "megacloud.tv",
    "streamwish.to",
    "filemoon.sx",
    "hubcloud.ist",
    "vidmoly.to",
    "turboviplay.com",
    "emturbovid.com",
    "neocdn.me",
    "animedekho.tv",
    "animedekho.app",
    "toonflix.in",
    "googleusercontent.com",
    "googleapis.com",
    "cloudfront.net",
    "akamaized.net",
    "xerver.xyz",
];

// NOTE: generic "*.workers.dev" is intentionally NOT allowlisted (V2 #22).
// Any Cloudflare Worker serving anime HLS must be added here explicitly by
// exact hostname after review — a blanket workers.dev allow lets any
// attacker worker pivot through the proxy (SSRF/open-redirect).

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

function isAllowedHost(hostname: string): boolean {
    const host = hostname.toLowerCase();
    if (ALLOWED_EXACT_HOSTS.has(host)) {
        return true;
    }
    for (const suffix of ALLOWED_SUFFIXES) {
        if (host === suffix || host.endsWith("." + suffix)) {
            return true;
        }
    }
    return false;
}

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

        // Must match the strict streaming/media allowlist
        return isAllowedHost(hostname);
    } catch {
        return false;
    }
}

// V2 #22: re-validate the FINAL URL after redirects. fetch() follows
// redirects by default, so an allowed initial URL could 302 to an internal
// or attacker host. Controllers must call this on response.url.
export function isValidFinalUrl(finalUrl: string): boolean {
    return isValidProxyUrl(finalUrl);
}
