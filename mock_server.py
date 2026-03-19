"""
mock_server.py — Simula los endpoints Hugo para pruebas locales.
Uso: python mock_server.py
"""
from flask import Flask, jsonify, request

app = Flask(__name__)

SINGLE_MD_ES = """---
title: "Europa en la Encrucijada: Cuando la Regulación se Convierte en Ventaja Competitiva"
date: 2026-03-17
draft: false
radar: true
description: "La convergencia de IA, Web3 y tecnologías cuánticas está redefiniendo la soberanía tecnológica europea, transformando la regulación de obstáculo en motor de innovación."
topics: ["ai", "web3", "quantum"]
areas: ["technology", "regulation", "governance"]
references:
  - title: "EU Council Agrees Position to Streamline Rules on AI"
    url: "https://www.consilium.europa.eu/en/press/press-releases/2026/03/13/council-agrees-position-to-streamline-rules-on-artificial-intelligence/"
    source: "consilium.europa.eu"
    image: "https://waiq.technology/images/upload/2026-03-16-a-turning-point.jpg"
  - title: "IQM to Become First Listed European Quantum Company"
    url: "https://www.cnbc.com/2026/02/23/finlands-iqm-listing-quantum-computing.html"
    source: "CNBC"
    image: "https://waiq.technology/images/upload/2026-03-16-iqm.jpg"
  - title: "AI and Blockchain Convergence: Opportunities, Risks and Governance"
    url: "https://seniorexecutive.com/ai-blockchain-convergence-opportunities-risk-governance/"
    source: "Senior Executive"
    image: ""
slug: "europa-encrucijada-regulacion-ventaja-competitiva"
---

El panorama tecnológico de 2026 presenta a Europa en una posición paradójica...
"""

SINGLE_MD_EN = """---
title: "Europe at the Crossroads: When Regulation Becomes Competitive Advantage"
date: 2026-03-17
draft: false
radar: true
description: "The convergence of AI, Web3 and quantum technologies is redefining European technological sovereignty, transforming regulation from obstacle to innovation driver."
topics: ["ai", "web3", "quantum"]
areas: ["technology", "regulation", "governance"]
references:
  - title: "EU Council Agrees Position to Streamline Rules on AI"
    url: "https://www.consilium.europa.eu/en/press/press-releases/2026/03/13/council-agrees-position-to-streamline-rules-on-artificial-intelligence/"
    source: "consilium.europa.eu"
    image: "https://waiq.technology/images/upload/2026-03-16-a-turning-point.jpg"
  - title: "IQM to Become First Listed European Quantum Company"
    url: "https://www.cnbc.com/2026/02/23/finlands-iqm-listing-quantum-computing.html"
    source: "CNBC"
    image: "https://waiq.technology/images/upload/2026-03-16-iqm.jpg"
slug: "europe-crossroads-regulation-competitive-advantage"
---

The technological landscape of 2026 presents Europe in a paradoxical position...
"""

DIGEST_DATA = {
    "total": 6,
    "button_urls": [
        "https://www.consilium.europa.eu/en/press/press-releases/2026/03/13/council-agrees-position-to-streamline-rules-on-artificial-intelligence/",
        "https://www.euractiv.com/section/digital/news/2026-03-06-eu-explores-legal-recognition-for-daos/",
        "https://thequantuminsider.com/2026/03/04/leaked-draft-reportedly-shows-quantum-among-technologies-removed-from-eu-industrial-policy-plan/",
        "https://www.forbes.com/sites/sabbirrangwala/2026/03/10/is-europe-poised-to-lead-the-quantum-computing-race/",
        "https://iapp.org/news/a/aesia-s-ai-guidelines-spain-steps-into-the-ai-spotlight",
        "https://www.cnbc.com/2026/02/18/europe-digital-sovereignty-geopolitical-tensions.html",
    ],
    "articles": [
        {
            "url": "https://www.consilium.europa.eu/en/press/press-releases/2026/03/13/council-agrees-position-to-streamline-rules-on-artificial-intelligence/",
            "title": "EU Council Agrees Position to Streamline Rules on Artificial Intelligence",
            "image": "https://waiq.technology/images/upload/2026-03-16-a-turning-point-for-blockchain-regulation-in-europe-gdpr-vs-immutability.jpg",
            "source": "consilium.europa.eu"
        },
        {
            "url": "https://www.euractiv.com/section/digital/news/2026-03-06-eu-explores-legal-recognition-for-daos/",
            "title": "EU Explores Legal Recognition for DAOs",
            "image": "https://waiq.technology/images/upload/2026-03-16-ai-regulation-2026.jpg",
            "source": "euractiv.com"
        },
        {
            "url": "https://thequantuminsider.com/2026/03/04/leaked-draft-reportedly-shows-quantum-among-technologies-removed-from-eu-industrial-policy-plan/",
            "title": "Quantum Among Technologies Removed from EU Industrial Policy Plan",
            "image": "https://waiq.technology/images/upload/2026-03-16-iqm.jpg",
            "source": "thequantuminsider.com"
        },
        {
            "url": "https://www.forbes.com/sites/sabbirrangwala/2026/03/10/is-europe-poised-to-lead-the-quantum-computing-race/",
            "title": "Is Europe Poised to Lead the Quantum Computing Race?",
            "image": "",
            "source": "forbes.com"
        },
        {
            "url": "https://iapp.org/news/a/aesia-s-ai-guidelines-spain-steps-into-the-ai-spotlight",
            "title": "AESIA's AI Guidelines: Spain Steps Into the AI Spotlight",
            "image": "",
            "source": "iapp.org"
        },
        {
            "url": "https://www.cnbc.com/2026/02/18/europe-digital-sovereignty-geopolitical-tensions.html",
            "title": "European Governments on Accelerating Digital Sovereignty",
            "image": "https://waiq.technology/images/upload/2026-03-16-sovereignty.jpg",
            "source": "cnbc.com"
        },
    ]
}


@app.get("/es/api/newsletter/single")
@app.get("/api/newsletter/single")
def single():
    lang = "es" if request.path.startswith("/es") else "en"
    print(f"→ GET single [{lang}]")
    md = SINGLE_MD_ES if lang == "es" else SINGLE_MD_EN
    return md, 200, {"Content-Type": "text/plain; charset=utf-8"}


@app.get("/es/api/newsletter/digest-<int:days>")
@app.get("/api/newsletter/digest-<int:days>")
def digest(days):
    lang = "es" if request.path.startswith("/es") else "en"
    print(f"→ GET digest [{lang}, {days}d]")
    data = dict(DIGEST_DATA)
    data["days"] = days
    return jsonify(data)


if __name__ == "__main__":
    print("🟢 Mock Hugo server en http://localhost:1313")
    print("   GET http://localhost:1313/es/api/newsletter/single")
    print("   GET http://localhost:1313/api/newsletter/single")
    print("   GET http://localhost:1313/es/api/newsletter/digest-15")
    print("   GET http://localhost:1313/es/api/newsletter/digest-30")
    print("   GET http://localhost:1313/api/newsletter/digest-15")
    app.run(port=1313, debug=False)
