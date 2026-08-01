$ErrorActionPreference = 'Stop'

$figureDirectory = $PSScriptRoot
$projectDirectory = Split-Path -Parent (Split-Path -Parent $figureDirectory)
$figureNames = @(
    'trusted_relay_candidate_example',
    'training_to_fpga_deployment',
    'ring6_environment',
    'physical_replay_setup',
    'resource_utilization_h0_h4'
)

Set-Location -LiteralPath $projectDirectory
if (-not (Test-Path -LiteralPath 'figures/new/nexys_img.jpg')) {
    & python 'figures/new/convert_nexys_image.py'
    if ($LASTEXITCODE -ne 0) {
        throw 'Nexys image conversion failed.'
    }
}

foreach ($figureName in $figureNames) {
    & xelatex -quiet -interaction=nonstopmode -file-line-error -halt-on-error `
        "-output-directory=$figureDirectory" "figures/new/$figureName.tex"
    if ($LASTEXITCODE -ne 0) {
        throw "Figure build failed: $figureName"
    }
}

Write-Output "Built $($figureNames.Count) vector figure PDFs in $figureDirectory."
