# RAISO Bot – Radiology AI Second Opinion App

RAISO (Radiology AI Second Opinion) is a minimal yet functional DICOM viewer powered by AI, designed to provide clinicians with a quick second opinion using open-source deep learning models. Built API-first and cloud-ready for healthcare use cases.

🛰️ **Live App**: [RAISO on Azure](https://raiso-container-app.ambitiousmoss-b2a629ad.westus.azurecontainerapps.io/)  
📖 **Behind the Scenes**: [Read the full story](https://shorthaired-cobweb-95c.notion.site/RAISO-Radiology-AI-Second-Opinion-App-on-Top-of-Azure-1f831893bffc80a385ddc16c3e76fd4c)  
🔑  **Request a Key**: [Contact me](mailto:contact@captaincto.com)

---

## 🚀 Running Locally (Docker, Port 8000)

```bash
git clone https://github.com/OmarLaham/RAISO-Bot.git
cd RAISO-Bot
docker build -t raiso .
docker run -p 8000:8000 raiso
