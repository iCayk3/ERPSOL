param(
  [Parameter(Mandatory=$true)][string]$Username,
  [Parameter(Mandatory=$true)][string]$Password,
  [Parameter(Mandatory=$true)][string]$Secret,
  [string]$ComposeRoot = "",
  [string]$WrongPassword = "senha-deliberadamente-incorreta"
)
$ErrorActionPreference = "Stop"
if (-not $ComposeRoot) { $ComposeRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path }
$files = @("-f", "$ComposeRoot/compose.yaml", "-f", "$ComposeRoot/overrides/compose.radius.yaml")
docker compose @files exec -T radius-primary radtest $Username $Password 127.0.0.1 0 $Secret | Select-String "Access-Accept" | Out-Null
docker compose @files exec -T radius-primary sh -lc "! radtest '$Username' '$WrongPassword' 127.0.0.1 0 '$Secret' | grep -q Access-Accept"
$session = "sol-lab-$([DateTimeOffset]::UtcNow.ToUnixTimeSeconds())"
$packets = @(
  "User-Name=$Username,Acct-Status-Type=Start,Acct-Session-Id=$session,NAS-IP-Address=127.0.0.1",
  "User-Name=$Username,Acct-Status-Type=Interim-Update,Acct-Session-Id=$session,NAS-IP-Address=127.0.0.1,Acct-Input-Octets=1024,Acct-Output-Octets=2048",
  "User-Name=$Username,Acct-Status-Type=Stop,Acct-Session-Id=$session,NAS-IP-Address=127.0.0.1,Acct-Session-Time=10"
)
foreach ($packet in $packets) {
  $packet | docker compose @files exec -T radius-primary radclient 127.0.0.1:1813 acct $Secret | Select-String "Accounting-Response" | Out-Null
}
Write-Host "RADIUS LAB OK: Access-Accept, Access-Reject e Start/Interim/Stop validados. Sessão $session"
