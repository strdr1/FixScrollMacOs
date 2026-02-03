# RDP Scroll Fixer for macOS

Fixes choppy or non-functional scrolling in Microsoft Remote Desktop (RDP) on Mac.

---

## 📥 1. Installation
1. Download **`RDP_Scroll_Fixer_Installer.dmg`**.
2. Open the file.
3. Drag the app icon into the **Applications** folder.

## 🚀 2. First Launch
**Important!** Since the app is not from the App Store, you must open it correctly the first time.

1. Go to your **Applications** folder.
2. Find **RDP Scroll Fixer**.
3. **Right-click** (or Control-click) the app.
4. Select **Open**.
5. Click **Open** in the confirmation dialog.

*(You only need to do this once).*

## 🔐 3. Permissions
The app requires Accessibility permissions to intercept and fix scroll events.

1. On launch, you will be prompted to grant **Accessibility** access.
2. Click to open System Settings.
3. Find **RDP Scroll Fixer** in the list and **enable the toggle/checkbox**.
   * *If it's already checked but not working, uncheck and re-check it.*

## ⚙️ Usage
The app runs in the menu bar.
* **Active** — Toggle the fix on/off.
* **Sensitivity** — Adjust scroll speed (1 = precise, 5 = fast).
* **Autostart** — Launch automatically on login.

Just run the app, switch to your RDP window, and scrolling should work smoothly.

## 📝 Logs (Troubleshooting)
The app writes a simple text log to help diagnose issues.
The file is located in your home directory:
`~/rdp_scroll_fixer.log` (or `/Users/YOUR_NAME/rdp_scroll_fixer.log`)

If you encounter issues, check this file for errors or scroll events.

## ⚠️ Troubleshooting

### "App is damaged" or "Operation not permitted" error
If macOS says the app is damaged, or Terminal says `zsh: operation not permitted`:
1. Open **Terminal**.
2. Paste this command and hit Enter:
   ```bash
   xattr -cr "/Applications/RDP Scroll Fixer.app"
   ```
3. The app will now launch correctly.

### App is running but scrolling is not fixed
Sometimes macOS permissions get stuck.
1. Go to **System Settings** -> **Privacy & Security** -> **Accessibility**.
2. Remove `RDP Scroll Fixer` from the list (using the minus button).
3. Restart the app and grant permissions again.

---

## 🛠 Build from Source (Terminal)
If you have the source code and want to build the app manually:

1. Open a terminal in the project folder.
   * *Tip: Type `cd ` (with a space) in Terminal, drag the project folder into the window, and hit Enter.*
2. Run the build script:
   ```bash
   sh build_installer.sh
   ```
3. The script will set up a virtual environment, install dependencies, and build the `.dmg`.
4. The installer will be in the `dist/` folder:
   `dist/RDP_Scroll_Fixer_Installer.dmg`
