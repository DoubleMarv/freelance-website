<?php
/**
 * Freelance Ireland – form relay to Brevo transactional email.
 * Keeps the Brevo API key server-side. Both forms post here.
 */

declare(strict_types=1);
header('Content-Type: application/json; charset=utf-8');

// ---- Config -------------------------------------------------------------
// Put the key in an env var, or in a file OUTSIDE the web root.
$apiKey    = getenv('xsmtpsib-d8428bb2ea1f2a2125d126ebba7ea646b84332c04a38821ae70cee8667692fdc-IG82PiErjE9ehBCH') ?: '';
// if (!$apiKey) { require __DIR__ . '/../brevo-config.php'; $apiKey = BREVO_API_KEY; }

$toEmail     = 'info@doublemarvellous.com';     // where submissions go
$toName      = 'Barry English';
$senderEmail = 'info@doublemarvellous.com'; // must be a verified sender in Brevo
$senderName  = 'Freelance Ireland website';
// -------------------------------------------------------------------------

function fail(int $code, string $msg): void {
    http_response_code($code);
    echo json_encode(['ok' => false, 'error' => $msg]);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') fail(405, 'Method not allowed');
if (!$apiKey) fail(500, 'Mail is not configured');

$in = $_POST;

// Honeypot: bots fill the hidden "website" field. Pretend success.
if (!empty($in['website'])) { echo json_encode(['ok' => true]); exit; }

$type  = ($in['form_type'] ?? '') === 'join' ? 'join' : 'hire';
$name  = trim((string)($in['name'] ?? ''));
$email = trim((string)($in['email'] ?? ''));
$details = trim((string)($in['details'] ?? ''));

if ($name === '' || mb_strlen($name) > 100)                 fail(422, 'Please enter your name.');
if (!filter_var($email, FILTER_VALIDATE_EMAIL))              fail(422, 'Please enter a valid email.');
if (mb_strlen($details) < 10 || mb_strlen($details) > 3000) fail(422, 'Please add a few more details.');
if (empty($in['consent']))                                   fail(422, 'Please tick the consent box.');

$fields = [
    'Name'  => $name,
    'Email' => $email,
];

if ($type === 'hire') {
    $subject = "New project enquiry – $name";
    $fields['Service'] = (string)($in['service'] ?? '');
    $fields['Budget']  = (string)($in['budget'] ?? '');
    $fields['Project'] = $details;
} else {
    $portfolio = trim((string)($in['portfolio'] ?? ''));
    if (!filter_var($portfolio, FILTER_VALIDATE_URL)) fail(422, 'Please enter a valid portfolio link.');
    $subject = "New freelancer application – $name";
    $fields['Main craft'] = (string)($in['service'] ?? '');
    $fields['Portfolio']  = $portfolio;
    $fields['About']      = $details;
}

$rows = '';
$text = '';
foreach ($fields as $label => $value) {
    $v = nl2br(htmlspecialchars($value, ENT_QUOTES, 'UTF-8'));
    $rows .= "<tr><td style=\"padding:6px 12px 6px 0;vertical-align:top;font-weight:600\">$label</td><td style=\"padding:6px 0\">$v</td></tr>";
    $text .= "$label: $value\n";
}
$html = "<html><body style=\"font-family:sans-serif\"><h2>" . htmlspecialchars($subject, ENT_QUOTES, 'UTF-8') . "</h2><table>$rows</table></body></html>";

$payload = [
    'sender'      => ['email' => $senderEmail, 'name' => $senderName],
    'to'          => [['email' => $toEmail, 'name' => $toName]],
    'replyTo'     => ['email' => $email, 'name' => $name],
    'subject'     => $subject,
    'htmlContent' => $html,
    'textContent' => $text,
    'tags'        => ['freelance-ireland', $type],
];

$ch = curl_init('https://api.brevo.com/v3/smtp/email');
curl_setopt_array($ch, [
    CURLOPT_POST           => true,
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT        => 15,
    CURLOPT_HTTPHEADER     => [
        'accept: application/json',
        'content-type: application/json',
        'api-key: ' . $apiKey,
    ],
    CURLOPT_POSTFIELDS     => json_encode($payload),
]);
$res    = curl_exec($ch);
$status = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

if ($status < 200 || $status >= 300) {
    error_log("Brevo send failed ($status): $res");
    fail(502, 'Sorry, something went wrong. Please try again.');
}

echo json_encode(['ok' => true]);
