# ☁️ VPS Deployment Guide for Trial Bot

This guide explains how to host your **Trial Bot** on a VPS (Virtual Private Server) so it runs 24/7.

## 📋 Prerequisites
1.  A VPS running **Ubuntu 20.04/22.04** or Debian.
2.  SSH access to your VPS.
3.  A new Bot Token for the trial version (recommended).

## 🚀 Deployment Steps

### 1. Upload Files to VPS
Since this is a custom trial version, you need to upload the files from your computer to the VPS.

**Using Command Line (SCP):**
Run this command from your computer (replace with your VPS details):
```bash
# Upload the whole folder to the VPS
scp -r "Ram-TG-BOT-auto-accepter-main" root@YOUR_VPS_IP:/home/root/
```
*Note: It's better to upload to a non-root user directory if available.*

**Using FileZilla (Easier):**
1.  Connect to your VPS using FileZilla (SFTP).
2.  Drag and drop the `Ram-TG-BOT-auto-accepter-main` folder to the `/home/username/` directory on the VPS.

### 2. Connect to VPS
SSH into your server:
```bash
ssh root@YOUR_VPS_IP
```

### 3. Run the Deployment Script
Navigate to the folder and run the auto-deployment script:

```bash
# Go to the folder
cd Ram-TG-BOT-auto-accepter-main

# Make the script executable
chmod +x deploy_trial_vps.sh

# Run it
./deploy_trial_vps.sh
```

**What the script does:**
-   Installs Python and necessary system tools.
-   Creates a virtual environment.
-   Installs bot dependencies.
-   Asks for your **Trial Bot Token**.
-   Sets up a background service (`telegram-bot-trial`) that automatically restarts if the bot crashes or the VPS reboots.

## 🛠️ Managing the Bot

Once deployed, use these commands on your VPS:

-   **Check Status:**
    ```bash
    sudo systemctl status telegram-bot-trial
    ```

-   **View Live Logs:**
    ```bash
    sudo journalctl -u telegram-bot-trial -f
    ```

-   **Restart Bot:**
    ```bash
    sudo systemctl restart telegram-bot-trial
    ```

-   **Stop Bot:**
    ```bash
    sudo systemctl stop telegram-bot-trial
    ```

## 🔄 Updating the Code
If you modify `bot_trial.py` locally:
1.  Upload the new `bot_trial.py` file to the VPS (overwrite the old one).
2.  Restart the service:
    ```bash
    sudo systemctl restart telegram-bot-trial
    ```
