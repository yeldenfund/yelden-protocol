# organize_repo.ps1
# Organiza a raiz do repo yelden-protocol
# Execute de dentro da pasta raiz do repo

$root = Get-Location
Write-Host "Organizando repo em: $root" -ForegroundColor Cyan

# ── CRIAR PASTAS ──────────────────────────────────────────────────────────────
$folders = @("docs", "scripts", ".github\workflows")
foreach ($f in $folders) {
    if (-not (Test-Path $f)) {
        New-Item -ItemType Directory -Path $f -Force | Out-Null
        Write-Host "  Criado: $f" -ForegroundColor Green
    }
}

# ── MOVER PARA /docs ──────────────────────────────────────────────────────────
$toDocs = @(
    "slither-report.txt",
    "gas-optimizations.md",
    "GITHUB_ISSUES.md",
    "coverage.json"
)
foreach ($f in $toDocs) {
    if (Test-Path $f) {
        Move-Item $f "docs\$f" -Force
        Write-Host "  docs\  ← $f" -ForegroundColor Yellow
    }
}

# ── MOVER PARA /scripts ───────────────────────────────────────────────────────
$toScripts = @(
    "abi_check.py",
    "check_agent.py",
    "find_abi.py",
    "fix_registry.py",
    "myfxbook_debug.py",
    "myfxbook_fetch.py",
    "fetch_myfxbook_local.py",
    "run-mutations-fixed.js",
    "restore_YeldenDistributor.ps1",
    "restore_YeldenVault.ps1",
    "restore_vault.ps1"
)
foreach ($f in $toScripts) {
    if (Test-Path $f) {
        Move-Item $f "scripts\$f" -Force
        Write-Host "  scripts\ ← $f" -ForegroundColor Yellow
    }
}

# ── MOVER ci.yml PARA .github/workflows ──────────────────────────────────────
if (Test-Path "ci.yml") {
    Move-Item "ci.yml" ".github\workflows\ci.yml" -Force
    Write-Host "  .github\workflows\ ← ci.yml" -ForegroundColor Yellow
}

# ── APAGAR LIXO ───────────────────────────────────────────────────────────────
$toDelete = @(
    "echo",
    "git",
    "ls",
    "npx",
    "python",
    "slither",
    "To",
    "test.spec",
    "hardhat.config.js.bak"
)
foreach ($f in $toDelete) {
    if (Test-Path $f) {
        Remove-Item $f -Force
        Write-Host "  Apagado: $f" -ForegroundColor Red
    }
}

# ── APAGAR DOCS WORD DA RAIZ ─────────────────────────────────────────────────
$wordFiles = @(
    "Aqui vai um rascunho completo e pronto para uso do Wyoming Alignment Addendum.docx",
    "The Yelden Scoring Model score.docx"
)
foreach ($f in $wordFiles) {
    if (Test-Path $f) {
        # Move para docs em vez de apagar — pode ser útil
        Move-Item $f "docs\$f" -Force
        Write-Host "  docs\  ← $f" -ForegroundColor Yellow
    }
}

# ── RESULTADO FINAL ───────────────────────────────────────────────────────────
Write-Host ""
Write-Host "Raiz do repo apos organizacao:" -ForegroundColor Cyan
Get-ChildItem -Name | Sort-Object

Write-Host ""
Write-Host "Concluido." -ForegroundColor Green
