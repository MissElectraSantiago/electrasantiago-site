<?php
// The "Send a note to Electra" boxes on the site post here.
// Each note is emailed to Electra through Hostinger. Nothing is stored.

const TO = 'electra@darknesscolorproject.com';
const FROM = 'notes@electrasantiago.com';
const HOSTS = ['electrasantiago.com', 'www.electrasantiago.com'];
const LIMIT = 5;          // notes per visitor...
const WINDOW = 600;       // ...every 10 minutes

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');

function done($code, $ok, $why = '') {
    http_response_code($code);
    echo json_encode($why === '' ? ['ok' => $ok] : ['ok' => $ok, 'error' => $why]);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    header('Allow: POST');
    done(405, false, 'post only');
}

// Only accept notes sent from the site's own pages
$from = $_SERVER['HTTP_ORIGIN'] ?? ($_SERVER['HTTP_REFERER'] ?? '');
$host = strtolower((string) parse_url($from, PHP_URL_HOST));
if (!in_array($host, HOSTS, true)) done(403, false, 'wrong site');

// The hidden box people can't see; bots fill it in. Pretend it worked.
if (trim($_POST['_gotcha'] ?? '') !== '' || trim($_POST['website'] ?? '') !== '') done(200, true);

function field($name, $max) {
    $v = trim((string) ($_POST[$name] ?? ''));
    $v = preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/u', '', $v);
    return mb_substr($v, 0, $max);
}
$message = field('message', 2000);
$email = field('email', 200);
$page = field('page', 80);
$view = field('view', 40);
if ($message === '') done(400, false, 'empty note');
if ($email !== '' && !filter_var($email, FILTER_VALIDATE_EMAIL)) $email = '';

// A few notes per visitor at most, so nobody can flood the inbox
$ip = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
$file = sys_get_temp_dir() . '/es-note-' . hash('sha256', $ip . __FILE__);
$now = time();
$times = array_filter(array_map('intval', explode(',', (string) @file_get_contents($file))), function ($t) use ($now) {
    return $t > $now - WINDOW;
});
if (count($times) >= LIMIT) done(429, false, 'too many notes');
$times[] = $now;
@file_put_contents($file, implode(',', $times), LOCK_EX);

if ($page === '') $page = $view === 'fashion' ? 'Community Resources (fashion map)' : 'Community Resources';
$one_line = function ($s) { return trim(preg_replace('/[\r\n]+/', ' ', $s)); };

$subject = 'Note from the website: ' . $one_line($page);
$body = $message . "\n\n---\n"
    . 'Page: ' . $one_line($page) . "\n"
    . 'Reply to: ' . ($email !== '' ? $email : 'no email given') . "\n"
    . 'Sent: ' . gmdate('j M Y, H:i') . " UTC\n";

$headers = [
    'From: Electra Santiago website <' . FROM . '>',
    'Content-Type: text/plain; charset=UTF-8',
    'MIME-Version: 1.0',
];
if ($email !== '') $headers[] = 'Reply-To: ' . $one_line($email);

$sent = mail(TO, '=?UTF-8?B?' . base64_encode($subject) . '?=', $body, implode("\r\n", $headers), '-f' . FROM);
if (!$sent) done(500, false, 'mail failed');
done(200, true);
