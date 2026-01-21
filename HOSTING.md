# Hosting & Deployment Guide

Since this application uses **Selenium (Chrome Automation)**, it requires a browser to run. This makes traditional web hosting (like Vercel/Netlify) unsuitable.

Here are the 3 ways to "Host" this:

## 1. Local Network Hosting (Best & Free)
You are already running it locally. To access it from other devices (like your phone or another laptop) on the same WiFi:
1. Run the app on your Mac (`./run_app.command`).
2. Look at the terminal output for the **Network URL** (e.g., `http://192.168.1.5:8501`).
3. Open that link on any device connected to the same WiFi.
4. **Note:** Your Mac must stay on and the app must be running.

## 2. One-Click Launch (For Daily Use)
I have created a file named `run_app.command` on your desktop.
- Double-click it to start the app instantly without opening the terminal.
- You might need to allow it in "System Settings > Privacy & Security" if Mac blocks it initially.

## 3. Cloud VPS (Advanced - For 24/7 Availability)
If you want to access this from anywhere (not just home WiFi), you need a **VPS (Virtual Private Server)**.
**Recommended:** AWS Lightsail, DigitalOcean, or Linode ($5-10/mo).

**Steps for Ubuntu VPS:**
1. **Install Chrome & Drivers:**
   ```bash
   sudo apt update
   sudo apt install -y google-chrome-stable
   ```
2. **Install Python & Requirements:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Run in Headless Mode (Tricky for WhatsApp):**
   WhatsApp Web *hates* headless browsers (browsers without a screen). It often bans them.
   **Solution:** Use a VPS with a GUI (Desktop) and use VNC/TeamViewer to log in and scan the QR Code.

## 4. Run on a dedicated "Bot" Laptop
The safest and easiest way for WhatsApp automation is to have an old laptop running this script 24/7 in the corner of your room.
- It mimics a real user perfectly.
- No extra server costs.
- No IP ban risks (uses your home IP).
