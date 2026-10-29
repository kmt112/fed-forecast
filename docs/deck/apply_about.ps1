# Replace slide 2 (About me) of the long deck with slide 2 of the short brief, which carries the owner's own edits
# (photo, wording). Run after `node build.js` and the copy to docs/FedCast_Fullerton.pptx; then export the PDF.
#   powershell -ExecutionPolicy Bypass -File docs/deck/apply_about.ps1
$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$long = Join-Path $root "docs\FedCast_Fullerton.pptx"
$short = Join-Path $root "docs\FedCast_Fullerton_short.pptx"
$pdf = Join-Path $root "docs\FedCast_Fullerton.pdf"
$app = New-Object -ComObject PowerPoint.Application
$pres = $app.Presentations.Open($long, $false, $false, $false)
$pres.Slides.Item(2).Delete()
$pres.Slides.InsertFromFile($short, 1, 2, 2) | Out-Null   # short deck's slide 2 becomes slide 2 of the long deck
$pres.Save()
$pres.SaveAs($pdf, 32)
if ($args.Count -gt 0) { $pres.Slides.Item(2).Export($args[0], "PNG", 1600, 900) }
$pres.Close()
$app.Quit()
Write-Output "about-me slide replaced; $pdf written"
