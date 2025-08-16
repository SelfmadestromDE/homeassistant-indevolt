# 🏠 Home Assistant Indevolt Integration

This is a custom integration for [Home Assistant](https://www.home-assistant.io/) that connects to an **Indevolt PowerFlex/SolidFlex 2000 and BK1600 Series** energy management system via HTTP. It allows you to monitor key metrics such as battery status, solar production, and grid import/export directly from your Home Assistant dashboard. This integration is read-only by now.

---

## ⚙️ Features

- 🔋 Battery percentage and voltage
- ☀️ Solar power production (Foreach MPPT)
- ⚡ Grid import/export monitoring
- much more....

## 📦 Installation with HACS

- Connect your unit directly with the indevolt App (Direct Device Connection)
- Enable local API (Settings --> Local API --> http)
- Note the IP Adress of the system (Network Settings --> Network IP)
- Add this repository as a custom repository in HACS and install
- Reboot HA
- Add as integration
- Type in the IP in "Host"
- Enjoy your Indevoltsystem in HA
