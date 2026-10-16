param(
    [string]$PythonExe = ""
)

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$ParentRoot = Split-Path -Parent $ProjectRoot
$PortableRoot = Join-Path $ParentRoot "vernaclear-portable"
$BuildRoot = Join-Path $ProjectRoot ".build"
$VenvRoot = Join-Path $BuildRoot "venv"
$StageRoot = Join-Path $BuildRoot "portable-stage"

function Resolve-Python {
    param([string]$Requested)
    $Candidates = @()
    if ($Requested) { $Candidates += $Requested }
    $Candidates += @(
        (Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\Python\Python311\python.exe"),
        "python"
    )
    foreach ($Candidate in $Candidates) {
        if (-not $Candidate) { continue }
        try {
            $Version = & $Candidate -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
            if ($LASTEXITCODE -eq 0 -and $Version -match '^3\.(11|12|13)$') {
                return $Candidate
            }
        } catch { }
    }
    throw "未找到 Python 3.11-3.13。请使用 -PythonExe 指定 python.exe。"
}

function Assert-ChildPath {
    param([string]$Parent, [string]$Child)
    $ResolvedParent = [System.IO.Path]::GetFullPath($Parent).TrimEnd('\') + '\'
    $ResolvedChild = [System.IO.Path]::GetFullPath($Child)
    if (-not $ResolvedChild.StartsWith($ResolvedParent, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "拒绝修改工作区之外的目录：$ResolvedChild"
    }
}

$Python = Resolve-Python $PythonExe
New-Item -ItemType Directory -Force -Path $BuildRoot | Out-Null
if (-not (Test-Path (Join-Path $VenvRoot "Scripts\python.exe"))) {
    & $Python -m venv $VenvRoot
}
$VenvPython = Join-Path $VenvRoot "Scripts\python.exe"
& $VenvPython -m pip install --disable-pip-version-check --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "pip 更新失败。" }
& $VenvPython -m pip install --disable-pip-version-check -r (Join-Path $ProjectRoot "requirements-dev.txt")
if ($LASTEXITCODE -ne 0) { throw "依赖安装失败。" }
& $VenvPython -m pytest (Join-Path $ProjectRoot "tests") -q --basetemp (Join-Path $BuildRoot "pytest-temp")
if ($LASTEXITCODE -ne 0) { throw "自动测试失败，已停止构建。" }

Assert-ChildPath $ProjectRoot $StageRoot
if (Test-Path $StageRoot) {
    Remove-Item -LiteralPath $StageRoot -Recurse -Force
}
$StageRuntime = Join-Path $StageRoot "runtime"
$StageLib = Join-Path $StageRuntime "Lib"
$StageSitePackages = Join-Path $StageLib "site-packages"
New-Item -ItemType Directory -Force -Path $StageRuntime | Out-Null

$BasePrefix = & $VenvPython -c "import sys; print(sys.base_prefix)"
if ($LASTEXITCODE -ne 0 -or -not (Test-Path (Join-Path $BasePrefix "pythonw.exe"))) {
    throw "无法定位 Python 基础运行环境。"
}

Copy-Item -LiteralPath (Join-Path $BasePrefix "python.exe") -Destination $StageRuntime
Copy-Item -LiteralPath (Join-Path $BasePrefix "pythonw.exe") -Destination $StageRuntime
Get-ChildItem -LiteralPath $BasePrefix -File -Include "python*.dll", "vcruntime*.dll", "LICENSE.txt" |
    Copy-Item -Destination $StageRuntime
Copy-Item -LiteralPath (Join-Path $BasePrefix "DLLs") -Destination $StageRuntime -Recurse
Copy-Item -LiteralPath (Join-Path $BasePrefix "Lib") -Destination $StageRuntime -Recurse
if (Test-Path $StageSitePackages) {
    Assert-ChildPath $StageRoot $StageSitePackages
    Remove-Item -LiteralPath $StageSitePackages -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $StageSitePackages | Out-Null

& $VenvPython -m pip install `
    --disable-pip-version-check `
    --no-compile `
    --target $StageSitePackages `
    -r (Join-Path $ProjectRoot "requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "便携环境依赖安装失败。" }

$AppRoot = Join-Path $StageRoot "app"
New-Item -ItemType Directory -Force -Path $AppRoot | Out-Null
Copy-Item -LiteralPath (Join-Path $ProjectRoot "src") -Destination $AppRoot -Recurse
Copy-Item -LiteralPath (Join-Path $ProjectRoot "run.py") -Destination $AppRoot
Copy-Item -LiteralPath (Join-Path $ProjectRoot "portable-readme.txt") -Destination (Join-Path $StageRoot "使用说明.txt")
Copy-Item -LiteralPath (Join-Path $ProjectRoot "packaging\Vernaclear.cmd") -Destination (Join-Path $StageRoot "Vernaclear.cmd")
New-Item -ItemType Directory -Force -Path (Join-Path $StageRoot "config"), (Join-Path $StageRoot "data"), (Join-Path $StageRoot "logs") | Out-Null

$LauncherSource = Join-Path $ProjectRoot "packaging\launcher.py"
$LauncherWork = Join-Path $BuildRoot "launcher-work"
$LauncherSpec = Join-Path $BuildRoot "launcher-spec"
& $VenvPython -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name "Vernaclear" `
    --distpath $StageRoot `
    --workpath $LauncherWork `
    --specpath $LauncherSpec `
    $LauncherSource
if ($LASTEXITCODE -ne 0) { throw "启动器生成失败。" }
$LauncherExe = Join-Path $StageRoot "Vernaclear.exe"
if (-not (Test-Path $LauncherExe)) { throw "启动器生成失败。" }

$env:VERNACLEAR_PORTABLE_ROOT = $StageRoot
& (Join-Path $StageRuntime "python.exe") (Join-Path $AppRoot "run.py") --self-test
if ($LASTEXITCODE -ne 0) { throw "便携版自检失败。" }
$SelfTestPath = Join-Path $StageRoot "logs\self-test.json"
$SelfTest = Get-Content -LiteralPath $SelfTestPath -Raw | ConvertFrom-Json
if ($SelfTest.status -ne "ok" -or $SelfTest.matches -lt 1) {
    throw "便携版自检结果异常。"
}
Remove-Item Env:\VERNACLEAR_PORTABLE_ROOT -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $SelfTestPath -Force

Assert-ChildPath $ParentRoot $PortableRoot
if (Test-Path $PortableRoot) {
    Remove-Item -LiteralPath $PortableRoot -Recurse -Force
}
Move-Item -LiteralPath $StageRoot -Destination $PortableRoot
Write-Host "便携版已生成并通过自检：$PortableRoot"
