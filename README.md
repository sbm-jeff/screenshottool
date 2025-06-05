# Screenshot tool voor apps in Apple en Android Stores

Deze tool genereert automatisch PNG-screenshots van diverse whitelabel apps op basis van SVG-templates en de kleurinstellingen uit de appconfigurator.

## 📂 Mappenstructuur

Zorg ervoor dat de mappenstructuur als volgt is opgezet:

```
project-root/
├── download-assets/
└── screenshottool/
    └── generate.py
```

* **download-assets/**
  Bevat de benodigde configuratiebestanden.

* **screenshottool/**
  Bevat de Python-tool (`generate.py`) voor het genereren van de screenshots en de SVG-templates.

## 🐍 Vereisten

* Python 3.x moet geïnstalleerd zijn.
* De benodigde dependencies (zoals `cairosvg`, `BeautifulSoup` ); 
Deze worden in de hoofd van generate.py bestand aangegeven met 'packages needed to install (pip install ...)'
Installeer deze met:

>
> ```bash
> pip install cairosvg
> ```

## ▶️ Gebruik

Voer het script uit met het volgende commando in de terminal:
alle flavors:

```bash
$ ./generate.py
```

met flavor
```bash
$ ./generate.py -f naamvanflavor
```

Dit script:

1. Leest SVG-templates uit `./mockup1.svg/`, `./mockup2.svg/`, `./mockup_ipad1.svg/`, `./mockup_ipad2.svg/`
2. Past de kleuren en eventueel teksten aan volgens de configuratie
3. Genereert PNG-afbeeldingen in de bijbehorende appkleuren

## 💡 Opmerkingen

* Zorg dat het script uitvoerbaar is met:

  ```bash
  chmod +x generate.py
  ```

* De gegenereerde afbeeldingen worden automatisch opgeslagen in een opgegeven uitvoermap (bijv. `{flavor}/`) binnen de `screenshottool`-map.

