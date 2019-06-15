
Add-Type -AssemblyName System.IO.Compression.FileSystem
function Unzip
{
    param([string]$zipfile, [string]$outpath)

    [System.IO.Compression.ZipFile]::ExtractToDirectory($zipfile, $outpath)
}

function DownloadLatest
{
    param([string]$url, [string]$outpath)
    
    # Download latest zip
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $down = New-Object System.Net.WebClient
    $down.DownloadFile($url, $outpath)
}

function SafeRemove
{
    param([string]$path)
    if (Test-Path $path)
    {
        echo "Removing existing $path"
        Remove-Item $path -recurse
    }
}

# Lotsa variables
$USER_DOWNLOADS_FOLDER = "$env:userprofile\Downloads"

$TOOL_GIT_REPO = "https://github.com/rBrenick/json-editor/archive/master.zip" # modify these after uploading the tool
$UPDATE_PATHS = @("docs", "json_editor", "README.md", "setup.py")

$CURRENT_TOOL_FOLDER = (Get-Item -Path ".").FullName
$CURRENT_json_editor = (Get-Item -Path ".").Name

$NEW_VERSION_ZIP = $USER_DOWNLOADS_FOLDER + "\" + $CURRENT_json_editor + "_update.zip"
$NEW_VERSION_ZIP_FOLDER = $USER_DOWNLOADS_FOLDER + "\" + $CURRENT_json_editor + "_update"

SafeRemove $NEW_VERSION_ZIP
SafeRemove $NEW_VERSION_ZIP_FOLDER

# Prompt at start just in case it was a mistype
$caption = "Get Latest Version";
$message = "This action will remove and rebuild the tool folders. `nAny changes to the scripts inside will be lost.`nContinue?`n ";
$Yes = new-Object System.Management.Automation.Host.ChoiceDescription "&Yes", "Yes";
$No = new-Object System.Management.Automation.Host.ChoiceDescription "&No", "No";
$choices = [System.Management.Automation.Host.ChoiceDescription[]]($Yes, $No);
$answer = $host.ui.PromptForChoice($caption,$message,$choices,0)

switch ($answer){
    0 {"Starting Update...";}
    1 {"Cancelling Update..."; exit}
}

# ------------------------------------------------
# RUN SCRIPT

# Download Zip file to User Downloads folder
echo "Downloading latest version to $NEW_VERSION_ZIP" 
DownloadLatest $TOOL_GIT_REPO $NEW_VERSION_ZIP
echo "Downloaded latest version to $NEW_VERSION_ZIP" 

# Unzip it to a folder with the same name
Unzip $NEW_VERSION_ZIP $NEW_VERSION_ZIP_FOLDER

echo ""
echo "Installing..."

# remove existing folders inside the current tool directory
foreach ($element in $UPDATE_PATHS) {
    $file_path = "$CURRENT_TOOL_FOLDER\$element"
    SafeRemove $file_path
}

# Copy new directories
foreach ($element in $UPDATE_PATHS) {
    # Since it's the latest version it will have -master suffix in the folder name
    $src_file_path = "$NEW_VERSION_ZIP_FOLDER\$CURRENT_json_editor-master\$element"
    $tgt_file_path = "$CURRENT_TOOL_FOLDER\$element"
    
    echo "Copying new $tgt_file_path"
    if (Test-Path $src_file_path) 
    {
        Copy-Item $src_file_path $tgt_file_path -recurse 
    }
}

# Cleanup the downloaded files
echo ""
echo "Cleaning up temp files..."
SafeRemove $NEW_VERSION_ZIP
SafeRemove $NEW_VERSION_ZIP_FOLDER

# Update Complete
echo ""
echo "Update complete. Please restart Maya"





