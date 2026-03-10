# =============================================================
# COA Converter App - Windows 构建脚本
# 用途：在 Windows 上构建可分发的 .exe 桌面应用
# =============================================================

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "+-----------------------------------------+" -ForegroundColor Blue
Write-Host "|   COA Converter App 构建 (Windows)       |" -ForegroundColor Blue
Write-Host "+-----------------------------------------+" -ForegroundColor Blue
Write-Host ""

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectDir

# ---- Step 1: 检查 Python ----
Write-Host "[1/5] " -ForegroundColor Yellow -NoNewline
Write-Host "检查 Python 环境..."

$PythonCmd = $null
foreach ($cmd in @("python3", "python")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "Python 3\.(1[2-9]|[2-9]\d)") {
            $PythonCmd = $cmd
            break
        }
    } catch {}
}

if (-not $PythonCmd) {
    Write-Host "  x 需要 Python 3.12+，请先安装。" -ForegroundColor Red
    Write-Host "  下载: https://www.python.org/downloads/"
    exit 1
}

$PythonVersion = & $PythonCmd --version 2>&1
Write-Host "  Python: $PythonVersion" -ForegroundColor Green

# ---- Step 2: 检查 coa-converter 后端 ----
Write-Host "[2/5] " -ForegroundColor Yellow -NoNewline
Write-Host "检查 coa-converter 后端模块..."

$CoaDir = Join-Path (Split-Path -Parent $ProjectDir) "coa-converter"
if (-not (Test-Path $CoaDir)) {
    $CoaDir = Join-Path $HOME "tools\coa-converter"
}

if (-not (Test-Path (Join-Path $CoaDir "coa_converter.py"))) {
    Write-Host "  x 未找到 coa-converter 后端模块。" -ForegroundColor Red
    Write-Host "  请确保 coa-converter 目录与 coa-converter-app 同级，" -ForegroundColor Yellow
    Write-Host "  或位于 ~/tools/coa-converter/" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  期望的目录结构:" -ForegroundColor Yellow
    Write-Host "    tools/" -ForegroundColor Yellow
    Write-Host "      coa-converter/        (后端)" -ForegroundColor Yellow
    Write-Host "      coa-converter-app/    (本项目)" -ForegroundColor Yellow
    exit 1
}

Write-Host "  后端路径: $CoaDir" -ForegroundColor Green

# ---- Step 3: 创建/更新虚拟环境 ----
Write-Host "[3/5] " -ForegroundColor Yellow -NoNewline
Write-Host "配置虚拟环境..."

$VenvDir = Join-Path $ProjectDir ".venv"
if (-not (Test-Path $VenvDir)) {
    Write-Host "  创建虚拟环境..."
    & $PythonCmd -m venv $VenvDir
}

$PipExe = Join-Path $VenvDir "Scripts\pip.exe"
$PythonExe = Join-Path $VenvDir "Scripts\python.exe"

Write-Host "  安装依赖..."
& $PipExe install --quiet --upgrade pip
& $PipExe install --quiet -r requirements.txt
& $PipExe install --quiet pyinstaller

Write-Host "  安装 coa-converter 后端依赖..."
$CoaReq = Join-Path $CoaDir "requirements.txt"
if (Test-Path $CoaReq) {
    & $PipExe install --quiet -r $CoaReq
} else {
    & $PipExe install --quiet pdfplumber openpyxl PyMuPDF python-docx
}

Write-Host "  依赖安装完成" -ForegroundColor Green

# ---- Step 4: 构建 ----
Write-Host "[4/5] " -ForegroundColor Yellow -NoNewline
Write-Host "使用 PyInstaller 构建..."

$SpecFile = Join-Path $ProjectDir "COA Converter Windows.spec"

# 清理旧构建
$BuildDir = Join-Path $ProjectDir "build"
$DistDir = Join-Path $ProjectDir "dist"
if (Test-Path $BuildDir) { Remove-Item -Path $BuildDir -Recurse -Force }
if (Test-Path $DistDir) { Remove-Item -Path $DistDir -Recurse -Force }

$PyInstallerExe = Join-Path $VenvDir "Scripts\pyinstaller.exe"
& $PyInstallerExe --noconfirm $SpecFile

if (-not (Test-Path (Join-Path $DistDir "COA Converter\COA Converter.exe"))) {
    Write-Host "  x 构建失败，请检查上方错误信息。" -ForegroundColor Red
    exit 1
}

Write-Host "  构建成功" -ForegroundColor Green

# ---- Step 5: 输出信息 ----
Write-Host "[5/5] " -ForegroundColor Yellow -NoNewline
Write-Host "打包完成！"

$OutputDir = Join-Path $DistDir "COA Converter"

Write-Host ""
Write-Host "+-----------------------------------------+" -ForegroundColor Green
Write-Host "|   构建完成！                              |" -ForegroundColor Green
Write-Host "+-----------------------------------------+" -ForegroundColor Green
Write-Host ""
Write-Host "输出目录: " -NoNewline
Write-Host $OutputDir -ForegroundColor Blue
Write-Host ""
Write-Host "使用方法:"
Write-Host "  1. 将 'dist\COA Converter' 整个文件夹复制到目标电脑"
Write-Host "  2. 双击 'COA Converter.exe' 运行"
Write-Host "  3. 在 Settings 标签页中配置模板目录路径"
Write-Host ""
Write-Host "提示: 首次运行可能被 Windows Defender 拦截，"
Write-Host "      点击 '更多信息' → '仍要运行' 即可。"
Write-Host ""
