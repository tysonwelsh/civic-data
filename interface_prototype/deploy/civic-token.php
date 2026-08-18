<?php
/**
 * Mint a short-lived token for the civic-data service.
 *
 * COPY THIS TO municipal-sky-site/api/civic-token.php.
 *
 * The browser never sees the shared secret — only a token that expires. This
 * file is the PHP half of a two-language contract: it MUST stay byte-compatible
 * with interface_prototype/agent/gate.py's _sign()/mint_token(). Both sides are
 * asserted against each other by interface_prototype/verify_token_parity.php.
 *
 * The contract, exactly:
 *   payload  = {"exp":<int>,"sub":"<string>"}   JSON, keys SORTED, no spaces
 *   body     = base64url(payload), '=' padding stripped
 *   token    = body . "." . base64url(hmac_sha256(body, secret)), padding stripped
 *
 * Two details that will silently break verification if changed: the JSON keys
 * are sorted (exp before sub) because Python emits them with sort_keys=True,
 * and base64url padding is stripped on BOTH segments.
 */

header('Content-Type: application/json');
header('Cache-Control: no-store');

// Secrets live outside the webroot — the site's existing convention.
$secrets_path = file_exists(__DIR__ . '/../config/secrets.php')
    ? __DIR__ . '/../config/secrets.php'                 // local development
    : '/home1/tdrivemy/private_config/secrets.php';      // production
$secrets = @include $secrets_path;

$secret   = $secrets['civic_service_secret'] ?? null;
$url_key  = $secrets['civic_url_key'] ?? null;   // the secret path segment
$endpoint = $secrets['civic_service_url'] ?? null;

if (empty($secret) || empty($url_key)) {
    http_response_code(500);
    echo json_encode(['error' => 'civic-data is not configured on this host']);
    exit();
}

/**
 * The gate is a SECRET URL with no password, so this endpoint must not become
 * an open token vending machine: it mints only when the caller proves it knows
 * the same secret path segment that served the page. hash_equals is
 * constant-time — a timing oracle here would leak the key character by
 * character.
 */
$provided = $_GET['k'] ?? ($_POST['k'] ?? '');
if (!is_string($provided) || !hash_equals($url_key, $provided)) {
    http_response_code(404);          // 404, not 403 — an unlisted page is not there
    echo json_encode(['error' => 'not found']);
    exit();
}

function civic_b64url(string $raw): string
{
    return rtrim(strtr(base64_encode($raw), '+/', '-_'), '=');
}

function civic_mint_token(string $secret, string $subject = 'web', int $ttl = 900): string
{
    // sort_keys=True on the Python side; JSON_UNESCAPED_SLASHES keeps the
    // encoder from differing on any subject containing a slash.
    $payload = ['exp' => time() + $ttl, 'sub' => $subject];
    ksort($payload);
    $body = civic_b64url(json_encode($payload, JSON_UNESCAPED_SLASHES));
    $sig  = civic_b64url(hash_hmac('sha256', $body, $secret, true));
    return $body . '.' . $sig;
}

$ttl = 900;
echo json_encode([
    'token'      => civic_mint_token($secret, 'web', $ttl),
    'expires_in' => $ttl,
    'endpoint'   => $endpoint,
]);
