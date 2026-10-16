# Installing and Managing SPS-CMS (Cross-Platform)

`sps-cms` is 100% cross-platform and natively supports **Windows (7, 8, 10, 11)**, **macOS**, and **Linux/WSL** across all major AI agent environments and skill package managers (`skills.sh`).

---

## ⚡ Method 1: Via Skills.sh CLI (`npx skills`)

If you use the universal `skills` CLI package manager:

```bash
npx skills add SHAHID8142/sps-cms
```

---

## 🪟 Method 2: Windows 1-Click Install (PowerShell)

Open PowerShell on Windows (Run as normal user or administrator) and execute:

```powershell
irm https://raw.githubusercontent.com/SHAHID8142/sps-cms/main/scripts/install.ps1 | iex
```

*(Works on Windows 7, 8, 10, and 11 with PowerShell 3.0, 5.1, or 7+)*

### Windows Update, Diagnostic & Uninstall
- **To Run Diagnostics:**
  ```powershell
  irm https://raw.githubusercontent.com/SHAHID8142/sps-cms/main/scripts/doctor.ps1 | iex
  ```
- **To Update:**
  ```powershell
  irm https://raw.githubusercontent.com/SHAHID8142/sps-cms/main/scripts/update.ps1 | iex
  ```
- **To Uninstall:**
  ```powershell
  irm https://raw.githubusercontent.com/SHAHID8142/sps-cms/main/scripts/uninstall.ps1 | iex
  ```

---

## 🍎 Method 3: macOS & 🐧 Linux / WSL 1-Click Install (Bash / Zsh)

Open Terminal and execute:

```bash
curl -fsSL https://raw.githubusercontent.com/SHAHID8142/sps-cms/main/scripts/install.sh | bash
```

### macOS/Linux Update, Diagnostic & Uninstall
- **To Run Diagnostics:**
  ```bash
  curl -fsSL https://raw.githubusercontent.com/SHAHID8142/sps-cms/main/scripts/doctor.sh | bash
  ```
- **To Update:**
  ```bash
  curl -fsSL https://raw.githubusercontent.com/SHAHID8142/sps-cms/main/scripts/update.sh | bash
  ```
- **To Uninstall:**
  ```bash
  curl -fsSL https://raw.githubusercontent.com/SHAHID8142/sps-cms/main/scripts/uninstall.sh | bash
  ```

---

## 🎯 Target Installation Locations

The installer automatically detects and deploys `sps-cms` to all installed coding agents:

| AI Host | Windows Path | macOS / Linux Path |
| :--- | :--- | :--- |
| **Antigravity (Gemini)** | `%USERPROFILE%\.gemini\config\skills\sps-cms` | `~/.gemini/config/skills/sps-cms` |
| **Claude Code** | `%USERPROFILE%\.claude\skills\sps-cms` | `~/.claude/skills/sps-cms` |
| **Cursor IDE** | `%USERPROFILE%\.cursor\skills\sps-cms` | `~/.cursor/skills/sps-cms` |
| **Windsurf / Cascade** | `%USERPROFILE%\.windsurf\skills\sps-cms` | `~/.windsurf/skills/sps-cms` |
| **Universal / Codex / Copilot** | `%USERPROFILE%\.agents\skills\sps-cms` | `~/.agents/skills/sps-cms` |
| **OpenCode** | `%USERPROFILE%\.config\opencode\skills\sps-cms` | `~/.config/opencode/skills/sps-cms` |
