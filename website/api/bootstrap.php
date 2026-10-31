<?php
declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');
header('Referrer-Policy: same-origin');

function respond(int $status, array $payload): never {
    http_response_code($status);
    echo json_encode($payload, JSON_UNESCAPED_SLASHES);
    exit;
}

function require_post(): array {
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') respond(405, ['ok' => false, 'message' => 'Method not allowed.']);
    $contentLength = (int)($_SERVER['CONTENT_LENGTH'] ?? 0);
    if ($contentLength < 1 || $contentLength > 32768) respond(413, ['ok' => false, 'message' => 'Invalid request size.']);
    $contentType = strtolower((string)($_SERVER['CONTENT_TYPE'] ?? ''));
    if (!str_starts_with($contentType, 'application/json')) respond(415, ['ok' => false, 'message' => 'JSON is required.']);
    enforce_same_origin();
    enforce_rate_limit();
    $body = json_decode((string)file_get_contents('php://input'), true);
    if (!is_array($body)) respond(400, ['ok' => false, 'message' => 'Invalid JSON.']);
    if (!empty($body['_website'])) respond(202, ['ok' => true]);
    return $body;
}

function enforce_same_origin(): void {
    $origin = (string)($_SERVER['HTTP_ORIGIN'] ?? '');
    if ($origin === '') return;
    $allowed = getenv('IMSUTH_ALLOWED_ORIGIN') ?: ('https://' . ($_SERVER['HTTP_HOST'] ?? 'www.imsuth.org'));
    if (!hash_equals(rtrim($allowed, '/'), rtrim($origin, '/'))) respond(403, ['ok' => false, 'message' => 'Origin not allowed.']);
}

function enforce_rate_limit(): void {
    $window = 600; $limit = 5; $now = time();
    $key = hash('sha256', (string)($_SERVER['REMOTE_ADDR'] ?? 'unknown'));
    $path = sys_get_temp_dir() . '/imsuth-form-' . $key . '.json';
    $handle = fopen($path, 'c+');
    if ($handle === false || !flock($handle, LOCK_EX)) respond(503, ['ok' => false, 'message' => 'Please try again shortly.']);
    $raw = stream_get_contents($handle); $hits = json_decode($raw ?: '[]', true);
    $hits = array_values(array_filter(is_array($hits) ? $hits : [], fn($time) => is_int($time) && $time > $now - $window));
    if (count($hits) >= $limit) { flock($handle, LOCK_UN); fclose($handle); respond(429, ['ok' => false, 'message' => 'Too many requests. Please wait and try again.']); }
    $hits[] = $now; ftruncate($handle, 0); rewind($handle); fwrite($handle, json_encode($hits)); fflush($handle); flock($handle, LOCK_UN); fclose($handle);
}

function text_field(array $data, string $key, int $min, int $max, bool $required = true): string {
    $value = trim((string)($data[$key] ?? '')); $length = mb_strlen($value);
    if (($required && $length < $min) || $length > $max) respond(422, ['ok' => false, 'field' => $key, 'message' => 'Please check this field.']);
    return $value;
}

function email_field(array $data, string $key): string {
    $value = text_field($data, $key, 3, 254);
    if (!filter_var($value, FILTER_VALIDATE_EMAIL)) respond(422, ['ok' => false, 'field' => $key, 'message' => 'Enter a valid email address.']);
    return $value;
}

function phone_field(array $data, string $key, bool $required = true): string {
    $value = text_field($data, $key, $required ? 10 : 0, 24, $required); $compact = preg_replace('/[\s\-()]/', '', $value);
    if ($value !== '' && !preg_match('/^(?:\+234|234|0)[789][01]\d{8}$/', $compact)) respond(422, ['ok' => false, 'field' => $key, 'message' => 'Enter a valid Nigerian phone number.']);
    return $value;
}

function deliver(string $formType, array $payload): void {
    $url = getenv('IMSUTH_FORM_WEBHOOK_URL'); $token = getenv('IMSUTH_FORM_WEBHOOK_TOKEN');
    if (!$url || !$token || !filter_var($url, FILTER_VALIDATE_URL) || !str_starts_with($url, 'https://')) respond(503, ['ok' => false, 'message' => 'Online submission is not currently configured.']);
    $envelope = json_encode(['formType' => $formType, 'submittedAt' => gmdate(DATE_ATOM), 'payload' => $payload], JSON_UNESCAPED_SLASHES);
    $curl = curl_init($url);
    curl_setopt_array($curl, [CURLOPT_POST => true, CURLOPT_POSTFIELDS => $envelope, CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 10, CURLOPT_HTTPHEADER => ['Content-Type: application/json', 'Authorization: Bearer ' . $token], CURLOPT_PROTOCOLS => CURLPROTO_HTTPS]);
    curl_exec($curl); $status = (int)curl_getinfo($curl, CURLINFO_RESPONSE_CODE); $error = curl_errno($curl); curl_close($curl);
    if ($error !== 0 || $status < 200 || $status >= 300) respond(502, ['ok' => false, 'message' => 'Submission could not be delivered.']);
    respond(202, ['ok' => true, 'message' => 'Your request has been received.']);
}
