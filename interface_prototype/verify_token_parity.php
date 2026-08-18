<?php
/**
 * Cross-language token check: PHP mints, Python must verify — and vice versa.
 *
 *     php interface_prototype/verify_token_parity.php
 *
 * This exists because the ripgrep engine shipped with a silent bug that only
 * appeared once the binary was installed: code written against a second
 * implementation, never executed against it, returned a confident wrong answer
 * rather than an error. The PHP/Python token contract has exactly that shape —
 * a mismatched byte produces "bad signature" in production and nowhere else —
 * so it gets asserted from both directions before it ever ships.
 */

$repo = dirname(__DIR__);
$secret = 'parity-test-secret';
$pass = 0;
$fail = 0;

function check(string $label, bool $ok, string $detail = ''): void
{
    global $pass, $fail;
    if ($ok) {
        $pass++;
        printf("  \033[32mPASS\033[0m  %-46s %s\n", $label, $detail);
    } else {
        $fail++;
        printf("  \033[31mFAIL\033[0m  %-46s %s\n", $label, $detail);
    }
}

function b64url(string $raw): string
{
    return rtrim(strtr(base64_encode($raw), '+/', '-_'), '=');
}

function mint(string $secret, string $subject = 'web', int $ttl = 900): string
{
    $payload = ['exp' => time() + $ttl, 'sub' => $subject];
    ksort($payload);
    $body = b64url(json_encode($payload, JSON_UNESCAPED_SLASHES));
    return $body . '.' . b64url(hash_hmac('sha256', $body, $secret, true));
}

/** Run a snippet against the Python gate with the same secret loaded. */
function python(string $repo, string $secret, string $code): string
{
    $script = "import sys; sys.path.insert(0, " . var_export($repo, true) . ")\n"
        . "from interface_prototype.agent import gate\n" . $code;
    $descriptors = [1 => ['pipe', 'w'], 2 => ['pipe', 'w']];
    $env = array_merge($_ENV, [
        'CIVIC_SERVICE_SECRET' => $secret,
        'PATH' => getenv('PATH'),
        'HOME' => getenv('HOME'),
    ]);
    $proc = proc_open(['python3', '-c', $script], $descriptors, $pipes, $repo, $env);
    if (!is_resource($proc)) {
        return 'SPAWN_FAILED';
    }
    $out = trim(stream_get_contents($pipes[1]));
    $err = trim(stream_get_contents($pipes[2]));
    foreach ($pipes as $p) {
        fclose($p);
    }
    proc_close($proc);
    return $out !== '' ? $out : ('ERR: ' . $err);
}

echo "\nToken parity — PHP mints, Python verifies. No API spend.\n\n";

// --- PHP -> Python -------------------------------------------------------
$token = mint($secret);
$lit = var_export($token, true);
$out = python($repo, $secret,
    "ok, sub, why = gate.verify_token($lit)\nprint('OK' if ok else 'NO:' + str(why), sub)");
check('Python accepts a PHP-minted token', str_starts_with($out, 'OK'), $out);

// --- Python -> PHP -------------------------------------------------------
$py_token = python($repo, $secret, "print(gate.mint_token('web'))");
[$body, $sig] = array_pad(explode('.', $py_token, 2), 2, '');
$expected = b64url(hash_hmac('sha256', $body, $secret, true));
check('PHP accepts a Python-minted token', hash_equals($expected, $sig),
      $sig === '' ? $py_token : 'signatures match');

// --- identical bytes for identical input ---------------------------------
// The real contract: the same payload must produce the same signature in both
// languages. Compare signatures over a FIXED body so the timestamp cannot differ.
$fixed_payload = json_encode(['exp' => 1893456000, 'sub' => 'web'], JSON_UNESCAPED_SLASHES);
$fixed_body = b64url($fixed_payload);
$php_sig = b64url(hash_hmac('sha256', $fixed_body, $secret, true));
$body_lit = var_export($fixed_body, true);
$py_sig = python($repo, $secret, "print(gate._sign($body_lit))");
check('signatures are byte-identical', $php_sig === $py_sig, "php=$php_sig py=$py_sig");

// The payload encoding itself must agree — sorted keys, no spaces.
$py_payload = python($repo, $secret,
    "import json; print(json.dumps({'exp':1893456000,'sub':'web'}, separators=(',',':'), sort_keys=True))");
check('payload JSON encodes identically', $fixed_payload === $py_payload,
      "php={$fixed_payload} py={$py_payload}");

// --- rejections ----------------------------------------------------------
$expired = mint($secret, 'web', -3600);
$exp_lit = var_export($expired, true);
$out = python($repo, $secret,
    "ok, _, why = gate.verify_token($exp_lit)\nprint('OK' if ok else 'NO:' + str(why))");
check('Python rejects an expired PHP token', str_starts_with($out, 'NO'), $out);

$wrong = mint('a-different-secret');
$wrong_lit = var_export($wrong, true);
$out = python($repo, $secret,
    "ok, _, why = gate.verify_token($wrong_lit)\nprint('OK' if ok else 'NO:' + str(why))");
check('Python rejects a foreign-secret token', str_starts_with($out, 'NO'), $out);

// --- the padding trap ----------------------------------------------------
// If either side forgot to strip '=' padding the tokens differ only for some
// payload lengths, so this would pass in testing and fail in production.
check('no base64 padding survives', !str_contains($token, '='), $token);

printf("\n  %d passed, %d failed\n\n", $pass, $fail);
exit($fail ? 1 : 0);
