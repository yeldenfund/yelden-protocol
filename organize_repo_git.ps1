# organize_repo_git.ps1
# Usa git mv para mover arquivos (respeita permissoes do Git)
# Execute de dentro da pasta raiz do repo

Write-Host "Organizando repo com git mv..." -ForegroundColor Cyan

# ── CRIAR PASTAS ──────────────────────────────────────────────────────────────
$folders = @("docs", "scripts", ".github/workflows")
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
        git mv $f "docs/$f"
        Write-Host "  docs/ <- $f" -ForegroundColor Yellow
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
        git mv $f "scripts/$f"
        Write-Host "  scripts/ <- $f" -ForegroundColor Yellow
    }
}

# ── MOVER ci.yml PARA .github/workflows ──────────────────────────────────────
if (Test-Path "ci.yml") {
    git mv "ci.yml" ".github/workflows/ci.yml"
    Write-Host "  .github/workflows/ <- ci.yml" -ForegroundColor Yellow
}

# ── MOVER DOCS WORD PARA /docs ────────────────────────────────────────────────
$wordFiles = @(
    "Aqui vai um rascunho completo e pronto para uso do Wyoming Alignment Addendum.docx",
    "The Yelden Scoring Model score.docx"
)
foreach ($f in $wordFiles) {
    if (Test-Path $f) {
        $safe = $f -replace ' ', '_'
        git mv $f "docs/$safe"
        Write-Host "  docs/ <- $f" -ForegroundColor Yellow
    }
}

# ── REMOVER LIXO COM git rm ───────────────────────────────────────────────────
$toDelete = @(
    "echo",
    "git",
    "ls",
    "npx",
    "python",
    "slither",
    "To",
    "test.spec",
    "hardhat.config.js.bak",
    "aderyn.config.zip",
    "echidna-test-2.0.5-Ubuntu-22.04.tar.gz"
)
foreach ($f in $toDelete) {
    if (Test-Path $f) {
        git rm -f $f 2>$null
        if (Test-Path $f) { Remove-Item $f -Force 2>$null }
        Write-Host "  Removido: $f" -ForegroundColor Red
    }
}

# ── RESULTADO ─────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "Status git:" -ForegroundColor Cyan
git status --short

Write-Host ""
Write-Host "Raiz apos organizacao:" -ForegroundColor Cyan
Get-ChildItem -Name | Where-Object { $_ -notmatch "^node_modules$|^artifacts$|^cache$|^coverage$|^crytic-export$|^\.certora" } | Sort-Object

Write-Host ""
Write-Host "Para commitar: git commit -m 'chore: reorganize repo structure'" -ForegroundColor Green
