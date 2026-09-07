<#
.SYNOPSIS
  dpa-codebase-reverse 静态校验脚本。

.DESCRIPTION
  校验 DPA 逆向 Skill 产物的结构、证据 Schema、稳定 ID 和确定性要求。
  校验范围：证据快照目录、证据记录、清单 manifest、覆盖率报告、审核队列。

.PARAMETER SnapshotDir
  证据快照目录（默认 evidence/snapshots）。

.PARAMETER EvidenceExamplesDir
  证据样例目录（默认 evidence/examples）。

.PARAMETER SchemaDir
  Schema 目录（默认 schemas/evidence）。

.EXAMPLE
  .\validate-dpa-reverse.ps1 -EvidenceExamplesDir evidence/examples -SchemaDir schemas/evidence
#>

[CmdletBinding()]
param(
    [string]$SnapshotDir = "evidence/snapshots",
    [string]$EvidenceExamplesDir = "evidence/examples",
    [string]$SchemaDir = "schemas/evidence"
)

$ErrorActionPreference = "Stop"
$failures = @()

function Write-Fail { param([string]$msg) $script:failures += $msg; Write-Host "FAIL: $msg" }
function Write-Ok { param([string]$msg) Write-Host "OK: $msg" }

# 定位 python
$python = $null
$cands = @(
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe"
)
foreach ($c in $cands) { if (Test-Path $c) { $python = $c; break } }
if (-not $python) {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { $python = $cmd.Source }
}
if (-not $python) {
    Write-Fail "找不到 Python（jsonschema 校验依赖）。请安装 Python 或指定 -Python 参数。"
} else {
    Write-Ok "Python: $python"
}

# 1. 目录存在性（snapshots 仅在真实扫描后生成，缺失不算失败）
foreach ($d in @($EvidenceExamplesDir, $SchemaDir)) {
    if (Test-Path $d) { Write-Ok "目录存在: $d" } else { Write-Fail "目录缺失: $d" }
}
if (Test-Path $SnapshotDir) { Write-Ok "快照目录存在: $SnapshotDir" } else { Write-Ok "快照目录尚未生成（真实扫描后出现）: $SnapshotDir" }

# 2. Schema 存在性
$schemaFiles = @(
    "evidence-record.schema.json",
    "snapshot-manifest.schema.json",
    "review-item.schema.json"
)
foreach ($s in $schemaFiles) {
    $p = Join-Path $SchemaDir $s
    if (Test-Path $p) { Write-Ok "Schema 存在: $s" } else { Write-Fail "Schema 缺失: $s" }
}

# 3. 样例存在性 + Schema 校验（通过临时 Python 脚本）
$pyCheck = @'
import json, sys, os
def validate(file, schema_file):
    data = json.load(open(file, encoding="utf-8"))
    if schema_file == "None" or not schema_file:
        return True, "json-ok"
    import jsonschema
    schema = json.load(open(schema_file, encoding="utf-8"))
    items = data if isinstance(data, list) else [data]
    for it in items:
        jsonschema.validate(it, schema)
    return True, "schema-ok"
ok = True
for file, schema_file in zip(sys.argv[1::2], sys.argv[2::2]):
    try:
        okk, msg = validate(file, schema_file)
        print(f"{msg}: {os.path.basename(file)}")
    except Exception as e:
        ok = False
        print(f"FAIL: {os.path.basename(file)}: {e}")
sys.exit(0 if ok else 1)
'@

$examples = @(
    @{ file = "evidence-records.json"; schema = "evidence-record.schema.json" },
    @{ file = "masterdata-snapshot-manifest.json"; schema = "snapshot-manifest.schema.json" },
    @{ file = "masterdata-review-queue.json"; schema = "review-item.schema.json" },
    @{ file = "masterdata-call-chain.json"; schema = "None" },
    @{ file = "masterdata-database-job-links.json"; schema = "None" },
    @{ file = "masterdata-ui-bindings.json"; schema = "None" },
    @{ file = "masterdata-coverage-report.json"; schema = "None" },
    @{ file = "masterdata-change-impact.json"; schema = "None" }
)

$tempDir = Join-Path $env:TEMP ("dpa-reverse-validate-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
$pyCheckFile = Join-Path $tempDir "check.py"
[System.IO.File]::WriteAllText($pyCheckFile, $pyCheck, [System.Text.Encoding]::UTF8)

$argList = @()
foreach ($ex in $examples) {
    $filePath = Join-Path $EvidenceExamplesDir $ex.file
    if (-not (Test-Path $filePath)) { Write-Fail "样例缺失: $($ex.file)"; continue }
    $schemaPath = Join-Path $SchemaDir $ex.schema
    if ($ex.schema -ne "None" -and -not (Test-Path $schemaPath)) {
        Write-Fail "样例 Schema 缺失: $($ex.schema)"; continue
    }
    $argList += "`"$filePath`""
    if ($ex.schema -ne "None") {
        $argList += "`"$schemaPath`""
    } else {
        $argList += "`"None`""
    }
}

if ($python -and $argList.Count -gt 0) {
    $checkInvoke = @($python, "`"$pyCheckFile`"") + $argList
    $output = & $python $pyCheckFile @($argList) 2>&1
    foreach ($line in $output) {
        if ($line -match '^OK|^json-ok|^schema-ok') { Write-Ok $line }
        elseif ($line -match '^FAIL') { Write-Fail $line }
    }
    if ($LASTEXITCODE -ne 0) { Write-Fail "样例 Schema 校验总体失败（exit $LASTEXITCODE）" }
    else { Write-Ok "样例 Schema 校验通过" }
}

# 4. 稳定 ID 确定性（evidence_id 不得含日期/绝对路径）
$idPattern = '^(ev|route|db|job|ui):[A-Za-z0-9_-]+:[A-Za-z0-9_.-]+:[A-Za-z0-9_./:-]+$'
Get-ChildItem -Path $EvidenceExamplesDir -Filter *.json -File | ForEach-Object {
    $content = Get-Content $_.FullName -Raw
    if ($content -match '"evidence_id"\s*:\s*"[^"]*\d{4}-\d{2}-\d{2}') {
        Write-Fail "证据 ID 含日期时间: $($_.Name)"
    }
}
Write-Ok "稳定 ID 无日期污染检查完成"

# 5. MIXED/HIGH 不被声明为可自动执行
$chainPath = Join-Path $EvidenceExamplesDir "masterdata-call-chain.json"
if (Test-Path $chainPath) {
    $chain = Get-Content $chainPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($chain.side_effect_classification.value -eq "MIXED" -and $chain.side_effect_classification.risk -eq "HIGH") {
        Write-Ok "MIXED/HIGH 已标注（禁止自动执行）"
    } else {
        Write-Fail "调用链样例未正确标注 MIXED/HIGH"
    }
}

# 清理临时文件
Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue

Write-Host ""
if ($failures.Count -gt 0) {
    Write-Host "校验失败: $($failures.Count) 项" -ForegroundColor Red
    exit 1
} else {
    Write-Host "校验通过" -ForegroundColor Green
    exit 0
}
