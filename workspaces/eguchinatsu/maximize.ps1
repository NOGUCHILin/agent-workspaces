Add-Type -Name Win -Namespace Native -MemberDefinition '[DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);'

$chrome = Get-Process -Name "chrome" -ErrorAction SilentlyContinue
if ($chrome) {
    foreach ($p in $chrome) {
        if ($p.MainWindowHandle -ne 0 -and $p.MainWindowTitle -like "*LINE*") {
            [Native.Win]::ShowWindow($p.MainWindowHandle, 3)
            Write-Host "Maximized: $($p.MainWindowTitle)"
        }
    }
} else {
    Write-Host "Chrome not found"
}
