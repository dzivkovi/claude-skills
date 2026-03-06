# ============================================================
# Anthropic Brand Fonts - Windows Setup Script
# Ships inside the branded-docx skill: scripts/setup/
#
# HOW TO RUN:
#   Right-click this file in File Explorer
#   Choose "Run with PowerShell"
#   Click Yes if Windows asks for permission
#
# WHAT IT DOES:
#   1. Checks whether Georgia is present (Windows built-in, usually fine)
#   2. Downloads Poppins (Regular, Bold, SemiBold, Italic, BoldItalic)
#      directly from Google's official GitHub repo
#   3. Installs system-wide if running as admin, per-user otherwise
#   4. Broadcasts WM_FONTCHANGE so running apps pick them up immediately
#
# WHEN TO RUN:
#   Once, before opening your first branded-docx document in Word.
#   No need to repeat unless you reinstall Windows or reset your user profile.
# ============================================================

$fontsNeeded = @(
    @{ Name = "Poppins Regular";    File = "Poppins-Regular.ttf";    Url = "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-Regular.ttf" },
    @{ Name = "Poppins Bold";       File = "Poppins-Bold.ttf";       Url = "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-Bold.ttf" },
    @{ Name = "Poppins SemiBold";   File = "Poppins-SemiBold.ttf";   Url = "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-SemiBold.ttf" },
    @{ Name = "Poppins Italic";     File = "Poppins-Italic.ttf";     Url = "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-Italic.ttf" },
    @{ Name = "Poppins BoldItalic"; File = "Poppins-BoldItalic.ttf"; Url = "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-BoldItalic.ttf" }
)

$systemFontsDir = "C:\Windows\Fonts"
$userFontsDir   = "$env:LOCALAPPDATA\Microsoft\Windows\Fonts"
$tempDir        = "$env:TEMP\anthropic-fonts"

Write-Host ""
Write-Host "=== Anthropic Brand Font Installer ===" -ForegroundColor Cyan
Write-Host ""

# Georgia check
$georgiaInstalled = (Test-Path "$systemFontsDir\georgia.ttf") -or (Test-Path "$systemFontsDir\GEORGIA.TTF")
if ($georgiaInstalled) {
    Write-Host "[OK] Georgia already installed (Windows built-in)" -ForegroundColor Green
} else {
    Write-Host "[INFO] Georgia not found - unusual. Run Windows Update > Optional Updates > Fonts if Word cannot find it." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "--- Checking Poppins ---" -ForegroundColor Cyan

$allInstalled = $true
foreach ($font in $fontsNeeded) {
    $systemPath = Join-Path $systemFontsDir $font.File
    $userPath   = Join-Path $userFontsDir   $font.File
    if ((Test-Path $systemPath) -or (Test-Path $userPath)) {
        Write-Host "[OK] $($font.Name) already installed" -ForegroundColor Green
    } else {
        Write-Host "[MISSING] $($font.Name)" -ForegroundColor Yellow
        $allInstalled = $false
    }
}

if ($allInstalled) {
    Write-Host ""
    Write-Host "All fonts already installed. Nothing to do." -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Downloading missing Poppins weights..." -ForegroundColor Cyan
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
            Write-Host " FAILED - check internet connection" -ForegroundColor Red
            continue
        }

        $installed = $false
        $isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]"Administrator")

        if ($isAdmin) {
            try {
                Copy-Item $destPath $systemFontsDir -Force
                $regPath  = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"
                Set-ItemProperty -Path $regPath -Name "$($font.Name) (TrueType)" -Value $font.File
                Write-Host "  [INSTALLED system-wide] $($font.Name)" -ForegroundColor Green
                $installed = $true
            } catch {
                Write-Host "  [WARN] System install failed, falling back to per-user..." -ForegroundColor Yellow
            }
        }

        if (-not $installed) {
            New-Item -ItemType Directory -Force -Path $userFontsDir | Out-Null
            Copy-Item $destPath $userFontsDir -Force
            $regPath = "HKCU:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"
            Set-ItemProperty -Path $regPath -Name "$($font.Name) (TrueType)" -Value (Join-Path $userFontsDir $font.File)
            Write-Host "  [INSTALLED per-user] $($font.Name)" -ForegroundColor Green
        }
    }

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
    Write-Host "Done. Restart Word if it was already open." -ForegroundColor Cyan
}

Write-Host ""
Write-Host "=== Complete ===" -ForegroundColor Cyan
Write-Host ""
pause
