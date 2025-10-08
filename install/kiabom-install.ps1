$KiABOM_install_path = $env:USERPROFILE + '\AppData\Local\kiabom\'
$KiABOM_exe_link = "https://github.com/Mage-Control-Systems-Ltd/KiABOM/releases/latest/download/kiabom.exe"
$KiABOM_config_link = "https://github.com/Mage-Control-Systems-Ltd/KiABOM/releases/latest/download/config.yaml"

Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

if (Test-Path -Path $KiABOM_install_path) {
    Write-Output "Removing previously installed executable and config file."
    Remove-Item $KiABOM_install_path -r # rm command
}

New-Item -Path $KiABOM_install_path -ItemType Directory | Out-Null # make new dir and suppress output
curl -fsSLO $KiABOM_exe_link
Move-Item kiabom.exe $KiABOM_install_path # mv command
Write-Output "Downloaded KiABOM executable." # echo command

curl -fsSLO $KiABOM_config_link
Move-Item config.yaml $KiABOM_install_path # mv command
Write-Output "Downloaded blank KiABOM API config.yaml." # echo command

$User_Env_Path_Value = Get-ItemProperty -Path 'HKCU:\Environment' -Name Path

# Change the backslashes to frontslashes so that -split can work
$KiABOM_install_path_frontslash = $KiABOM_install_path -replace "\\","/"
$User_Env_Path_Value_frontslash = $User_Env_Path_Value.Path -replace "\\", "/"

# Check if the install path exists by splitting the Path variable value
$KiABOM_path_check = $User_Env_Path_Value_frontslash -split $KiABOM_install_path_frontslash | Measure-Object 

if ($KiABOM_path_check.Count -igt 1) {
    Write-Output "Detected previous KiABOM installation."
    Write-Output "Nothing was added to the user Path variable."
} else {
    Write-Output "Detected no previous KiABOM install."
    Write-Output "Adding executable to user Path environment variable."
    $New_Path_Value = $User_Env_Path_Value.Path + ";" + $KiABOM_install_path + ";" 
    Set-ItemProperty -Path 'HKCU:\Environment' -Name Path -Value $New_Path_Value # set the system environment variable for KiABOM
}

Write-Output "Succesfully installed KiABOM."

Read-Host "Press Enter to finish"

Exit
