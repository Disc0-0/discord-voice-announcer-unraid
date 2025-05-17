# PowerShell script for setting up Discord Voice Announcer on Windows

# Function to output colored text
function Write-ColorOutput {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Message,
        
        [Parameter(Mandatory=$false)]
        [string]$ForegroundColor = "White"
    )
    
    $originalColor = $Host.UI.RawUI.ForegroundColor
    $Host.UI.RawUI.ForegroundColor = $ForegroundColor
    Write-Output $Message
    $Host.UI.RawUI.ForegroundColor = $originalColor
}

Write-ColorOutput "Setting up Discord Voice Announcer with Web Interface..." "Green"

# Create data directory if it doesn't exist
if (-not (Test-Path -Path ".\data")) {
    New-Item -Path ".\data" -ItemType Directory | Out-Null
    Write-ColorOutput "Created data directory" "Green"
}

# Check if .env file exists, create from example if not
if (-not (Test-Path -Path ".\.env")) {
    if (Test-Path -Path ".\.env.example") {
        Copy-Item -Path ".\.env.example" -Destination ".\.env"
        Write-ColorOutput "Created .env file from example. Please edit it to add your Discord bot token." "Yellow"
    } else {
        Write-ColorOutput "Error: .env.example file not found. Please create a .env file manually." "Red"
        exit 1
    }
}

# Get Docker group ID (this is more relevant for Linux, but keeping for consistency)
Write-ColorOutput "Note: Docker group ID is not typically used on Windows. Using default value." "Yellow"
$dockerGid = 999

# Add Docker GID to .env file if not already present
$envContent = Get-Content -Path ".\.env" -Raw
if (-not ($envContent -match "DOCKER_GID=")) {
    Add-Content -Path ".\.env" -Value "`n# Docker GID for web interface permissions`nDOCKER_GID=$dockerGid"
    Write-ColorOutput "Added DOCKER_GID to .env file" "Green"
} else {
    # Update existing DOCKER_GID value - more involved in PowerShell
    $envContent = $envContent -replace "DOCKER_GID=.*", "DOCKER_GID=$dockerGid"
    $envContent | Set-Content -Path ".\.env"
    Write-ColorOutput "Updated DOCKER_GID in .env file" "Green"
}

# Prompt to edit .env file
Write-ColorOutput "Please make sure to edit your .env file to add your Discord bot token." "Yellow"
$editNow = Read-Host "Do you want to edit the .env file now? (y/n)"
if ($editNow -eq "y" -or $editNow -eq "Y") {
    notepad.exe ".\.env"
}

# Start containers
Write-ColorOutput "Starting containers..." "Green"
docker-compose up -d

# Show status
Write-ColorOutput "Setup complete!" "Green"
Write-ColorOutput "Discord Voice Announcer bot and Web Interface should now be running." "Green"
Write-ColorOutput "Access the web interface at http://localhost:5000" "Green"
Write-ColorOutput "If you experience any issues, check the logs with: docker-compose logs" "Yellow"

