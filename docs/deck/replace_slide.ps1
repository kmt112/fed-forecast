# Replace one slide of the owner's edited deck with the same-titled slide from a fresh build, keeping every other
# edit the owner made in PowerPoint. Usage:
#   powershell -ExecutionPolicy Bypass -File docs/deck/replace_slide.ps1 -Target <n in the owner's deck> -Source <n in the build> [-Png path]
param([int]$Target, [int]$Source, [string]$Png)
$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$deck = Join-Path $root "docs\FedCast_Fullerton.pptx"
$build = Join-Path $PSScriptRoot "FedCast_Fullerton.pptx"
$pdf = Join-Path $root "docs\FedCast_Fullerton.pdf"
$app = New-Object -ComObject PowerPoint.Application
$pres = $app.Presentations.Open($deck, $false, $false, $false)
$pres.Slides.Item($Target).Delete()
$pres.Slides.InsertFromFile($build, $Target - 1, $Source, $Source) | Out-Null
$pres.Save()
$pres.SaveAs($pdf, 32)
if ($Png) { $pres.Slides.Item($Target).Export($Png, "PNG", 1600, 900) }
$pres.Close()
$app.Quit()
Write-Output "slide $Target replaced from build slide $Source; $pdf written"
