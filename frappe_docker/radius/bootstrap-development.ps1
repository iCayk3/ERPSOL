param(
  [string]$Site = "development.localhost",
  [string]$BenchContainer = "devcontainer-example-frappe-1",
  [string]$DockerNetwork = "devcontainer-example_default",
  [string]$LabNetwork = "127.0.0.1/32"
)

$ErrorActionPreference = "Stop"
$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$FrappeDocker = Join-Path $RepositoryRoot "frappe_docker"
$dockerCandidates = @(
  (Get-Command docker -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue),
  "$env:LOCALAPPDATA\Programs\DockerDesktop\resources\bin\docker.exe",
  "$env:ProgramFiles\Docker\Docker\resources\bin\docker.exe"
) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }
if (-not $dockerCandidates) { throw "Docker CLI não encontrado. Instale/inicie o Docker Desktop antes de continuar." }
$Docker = $dockerCandidates[0]

& $Docker info *> $null
if ($LASTEXITCODE -ne 0) { throw "Docker Desktop foi encontrado, mas o daemon Linux não está disponível." }
& $Docker inspect $BenchContainer *> $null
if ($LASTEXITCODE -ne 0) { throw "Container $BenchContainer não encontrado. Inicie primeiro devcontainer-example." }
& $Docker network inspect $DockerNetwork *> $null
if ($LASTEXITCODE -ne 0) { throw "Rede $DockerNetwork não encontrada. Confirme o projeto Docker do bench." }

function Get-OrCreateUserSecret([string]$Name) {
  $value = [Environment]::GetEnvironmentVariable($Name, "User")
  if (-not $value) {
    $bytes = New-Object byte[] 32
    [Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
    $value = [Convert]::ToBase64String($bytes)
    [Environment]::SetEnvironmentVariable($Name, $value, "User")
  }
  Set-Item -Path "Env:$Name" -Value $value
  return $value
}

$dbPassword = Get-OrCreateUserSecret "RADIUS_DB_PASSWORD"
$null = Get-OrCreateUserSecret "RADIUS_DB_ROOT_PASSWORD"
$null = Get-OrCreateUserSecret "RADIUS_LAB_SECRET"
$env:RADIUS_LAB_NETWORK = $LabNetwork
$env:ERP_DOCKER_NETWORK = $DockerNetwork
$env:ERPNEXT_VERSION = "v16"
[Environment]::SetEnvironmentVariable("RADIUS_LAB_NETWORK", $LabNetwork, "User")
[Environment]::SetEnvironmentVariable("ERP_DOCKER_NETWORK", $DockerNetwork, "User")

$compose = @(
  "compose", "--profile", "radius-ha", "--project-directory", $FrappeDocker,
  "-f", (Join-Path $FrappeDocker "compose.yaml"),
  "-f", (Join-Path $FrappeDocker "overrides\compose.radius.yaml")
)
& $Docker @compose up -d --build radius-db radius-primary radius-secondary
if ($LASTEXITCODE -ne 0) { throw "Falha ao iniciar a stack RADIUS." }

$benchRoot = "/workspace/development/frappe-bench"
& $Docker exec -w $benchRoot $BenchContainer bench --site $Site set-config radius_db_host frappe_docker-radius-db-1
& $Docker exec -w $benchRoot $BenchContainer bench --site $Site set-config radius_db_port 3306
& $Docker exec -w $benchRoot $BenchContainer bench --site $Site set-config radius_db_name radius
& $Docker exec -w $benchRoot $BenchContainer bench --site $Site set-config radius_db_user radius_app
& $Docker exec -w $benchRoot $BenchContainer bench --site $Site set-config radius_db_password $dbPassword
& $Docker exec -w $benchRoot $BenchContainer bench --site $Site migrate
if ($LASTEXITCODE -ne 0) { throw "Falha na migração do site." }

& $Docker exec -w $benchRoot $BenchContainer bench --site $Site execute sol_brasil.radius_provisioning.migration_audit
& $Docker exec -w $benchRoot $BenchContainer bench --site $Site execute sol_brasil.radius_provisioning.synchronize_nas
& $Docker exec -w $benchRoot $BenchContainer bench --site $Site execute sol_brasil.radius_provisioning.reconcile_radius
$kwargs = '{"limit": 1000}'
& $Docker exec -w $benchRoot $BenchContainer bench --site $Site execute sol_brasil.radius_provisioning.process_pending_events --kwargs $kwargs
& $Docker exec -w $benchRoot $BenchContainer bench --site $Site execute sol_brasil.radius_provisioning.radius_health

Write-Host "Implantação RADIUS concluída. Segredos próprios foram mantidos no perfil do Windows e não foram gravados no Git."
