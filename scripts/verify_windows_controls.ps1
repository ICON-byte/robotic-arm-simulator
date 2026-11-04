param([Parameter(Mandatory=$true)][int]$ApplicationProcessId)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$scope = [System.Windows.Automation.TreeScope]::Descendants
$condition = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ProcessIdProperty, $ApplicationProcessId)
$window = [System.Windows.Automation.AutomationElement]::RootElement.FindFirst([System.Windows.Automation.TreeScope]::Children, $condition)
if ($null -eq $window) { throw 'Application accessibility root not found' }
$runtimeModules = @((Get-Process -Id $ApplicationProcessId).Modules | ForEach-Object { $_.FileName })
if ($runtimeModules | Where-Object { $_ -match '\\\.venv\\|\\src\\robotic_arm_simulator\\' }) { throw 'Development runtime loaded by frozen application' }
if (-not ($runtimeModules | Where-Object { $_ -match '_internal\\python312.dll$' })) { throw 'Bundled Python runtime not loaded' }
function Control([string]$Name) {
    $match = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::NameProperty, $Name)
    $element = $window.FindFirst($scope, $match)
    if ($null -eq $element) { throw "Control missing: $Name" }
    return $element
}
function Invoke-Control([string]$Name) {
    (Control $Name).GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke()
    Start-Sleep -Milliseconds 120
}
function Select-Tab([string]$Name) {
    (Control $Name).GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern).Select()
}
$clipboardBefore = Get-Clipboard -Raw
try {
    foreach ($joint in @('Base', 'Shoulder', 'Elbow')) {
        (Control "$joint angle in degrees").GetCurrentPattern([System.Windows.Automation.RangeValuePattern]::Pattern).SetValue(0)
    }
    Invoke-Control 'Copy results'
    if ((Get-Clipboard -Raw) -notmatch 'X: 350.000 mm') { throw 'Live FK/clipboard did not update' }
    Select-Tab ('4 ' + [char]0x00D7 + ' 4 matrix')
    if ((Control 'Tool-to-world matrix row 1, column 4').Current.IsOffscreen) { throw 'Matrix is not visible' }
    Select-Tab 'Coordinates'
    Select-Tab 'IK target'
    foreach ($pair in @(@('X','250'), @('Y','50'), @('Z','150'))) {
        (Control "Target $($pair[0]) coordinate in millimetres").GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).SetValue($pair[1])
    }
    Invoke-Control 'Calculate IK'
    Invoke-Control 'Apply now'
    Invoke-Control 'Copy results'
    $copied = Get-Clipboard -Raw
    if ($copied -notmatch 'X: 250.000 mm' -or $copied -notmatch 'Y: 50.000 mm' -or $copied -notmatch 'Z: 150.000 mm') { throw 'IK apply/clipboard failed' }
    (Control 'Target X coordinate in millimetres').GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).SetValue('0')
    (Control 'Target Y coordinate in millimetres').GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).SetValue('300')
    Invoke-Control 'Calculate IK'
    Invoke-Control 'Animate'
    Invoke-Control 'Pause'
    if (-not (Control 'Resume').Current.IsEnabled) { throw 'Pause did not change transport state' }
    Invoke-Control 'Resume'
    Invoke-Control 'Stop'
    Invoke-Control 'Reset arm'
    Invoke-Control 'Load selected demonstration preset'
    Invoke-Control 'Reset view'
    Write-Output 'PASS: packaged FK, sliders, matrix, IK, clipboard, motion transport, reset, preset load'
} finally {
    Set-Clipboard -Value ([string]$clipboardBefore)
}
