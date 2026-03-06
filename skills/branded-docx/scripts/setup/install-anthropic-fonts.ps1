# ============================================================
# Anthropic Brand Fonts - Install Script
# Checks for Poppins + Georgia, installs what is missing.
# Run: Right-click > "Run with PowerShell"
# ============================================================

$fontsNeeded = @(
    @{ Name = "Poppins Regular";   File = "Poppins-Regular.ttf";  Url = "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-Regular.ttf" },
    @{ Name = "Poppins Bold";      File = "Poppins-Bold.ttf";     Url = "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-Bold.ttf" },
    @{ Name = "Poppins SemiBold";  File = "Poppins-SemiBold.ttf"; Url = "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-SemiBold.ttf" },
    @{ Name = "Poppins Italic";    File = "Poppins-Italic.ttf";   Url = "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-Italic.ttf" },
    @{ Name = "Poppins BoldItalic";File = "Poppins-BoldItalic.ttf";Url = "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-BoldItalic.ttf" }
)

$systemFontsDir = "C:\Windows\Fonts"
$userFontsDir   = "$env:LOCALAPPDATA\Microsoft\Windows\Fonts"
$tempDir        = "$env:TEMP\anthropic-fonts"

Write-Host ""
Write-Host "=== Anthropic Brand Font Installer ===" -ForegroundColor Cyan
Write-Host ""

# ------ Georgia check ------
$georgiaInstalled = (Test-Path "$systemFontsDir\georgia.ttf") -or (Test-Path "$systemFontsDir\GEORGIA.TTF")
if ($georgiaInstalled) {
    Write-Host "[OK] Georgia is already installed (Windows built-in)" -ForegroundColor Green
} else {
    Write-Host "[INFO] Georgia not found in system fonts - this is unusual. It ships with Windows by default." -ForegroundColor Yellow
    Write-Host "       If Word still cannot find it, run: Windows Update > Optional Updates > Fonts" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "--- Checking Poppins ---" -ForegroundColor Cyan

# ------ Poppins check and install ------
$allInstalled = $true
foreach ($font in $fontsNeeded) {
    $systemPath = Join-Path $systemFontsDir $font.File
    $userPath   = Join-Path $userFontsDir   $font.File
    if ((Test-Path $systemPath) -or (Test-Path $userPath)) {
        Write-Host "[OK] $($font.Name) already installed" -ForegroundColor Green
    } else {
        Write-Host "[MISSING] $($font.Name) - will install" -ForegroundColor Yellow
        $allInstalled = $false
    }
}

if ($allInstalled) {
    Write-Host ""
    Write-Host "All fonts already installed. Nothing to do." -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Downloading missing Poppins weights..." -ForegroundColor Cyan

    # Create temp dir
    New-Item -ItemType Directory -Force -Path $tempDir | Out-Null

    foreach ($font in $fontsNeeded) {
        $systemPath = Join-Path $systemFontsDir $font.File
        $userPath   = Join-Path $userFontsDir   $font.File
        if ((Test-Path $systemPath) -or (Test-Path $userPath)) { continue }

        $destPath = Join-Path $tempDir $font.File
        Write-Host "  Downloading $($font.Name)..." -NoNewline

        try {
            Invoke-WebRequest -Uri $font.Url -OutFile $destPath -UseBasicParsing
            Write-Host " done" -ForegroundColor Green
        } catch {
            Write-Host " FAILED - check your internet connection" -ForegroundColor Red
            continue
        }

        # Try system-wide install first (needs admin), fall back to per-user
        $installed = $false

        if (([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]"Administrator")) {
            try {
                Copy-Item $destPath $systemFontsDir -Force
                $regPath = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"
                $fontName = $font.Name + " (TrueType)"
                Set-ItemProperty -Path $regPath -Name $fontName -Value $font.File
                Write-Host "  [INSTALLED system-wide] $($font.Name)" -ForegroundColor Green
                $installed = $true
            } catch {
                Write-Host "  [WARN] System install failed, trying per-user..." -ForegroundColor Yellow
            }
        }

        if (-not $installed) {
            # Per-user install (no admin needed)
            New-Item -ItemType Directory -Force -Path $userFontsDir | Out-Null
            Copy-Item $destPath $userFontsDir -Force
            $regPath = "HKCU:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"
            $fontName = $font.Name + " (TrueType)"
            Set-ItemProperty -Path $regPath -Name $fontName -Value (Join-Path $userFontsDir $font.File)
            Write-Host "  [INSTALLED per-user] $($font.Name)" -ForegroundColor Green
        }
    }

    # Broadcast WM_FONTCHANGE so apps pick up new fonts without restarting
    Add-Type -TypeDefinition @"
    using System;
    using System.Runtime.InteropServices;
    public class FontHelper {
        [DllImport("user32.dll")] public static extern int SendMessage(IntPtr hWnd, int msg, int wParam, int lParam);
        public static readonly IntPtr HWND_BROADCAST = new IntPtr(0xffff);
        public const int WM_FONTCHANGE = 0x1D;
    }
"@
    [FontHelper]::SendMessage([FontHelper]::HWND_BROADCAST, [FontHelper]::WM_FONTCHANGE, 0, 0) | Out-Null

    Write-Host ""
    Write-Host "Installation complete. Restart Word if it was open." -ForegroundColor Cyan
}

Write-Host ""
Write-Host "=== Done ===" -ForegroundColor Cyan
Write-Host ""
pause
