# TerraGuard AI — Hardware

`Auteur` Rares-Stefan Delamarian

## Description

Ce projet consiste à réaliser un dispositif de surveillance de la santé des sols capable de mesurer en temps réel l'humidité, le pH et la luminosité de l'environnement. Les capteurs collectent les données en continu et les transmettent via une connexion Wi-Fi à un broker RabbitMQ, où elles sont ensuite traitées par un modèle de machine learning pour évaluer la qualité du sol et recommander des cultures adaptées. C'est un projet pratique pour surveiller la santé agricole de manière autonome et à faible coût.

## Motivation

La qualité du sol est un facteur déterminant pour la réussite des cultures, mais son évaluation reste souvent manuelle, coûteuse et peu fréquente. La principale motivation de ce projet est de créer un système de surveillance continu, accessible et automatisé. D'un point de vue éducatif, ce projet permet d'explorer les bases de l'Internet des Objets (IoT) en apprenant à interfacer plusieurs capteurs environnementaux avec un microcontrôleur et à établir une communication sans fil avec un backend de traitement de données.

## Architecture

### Schéma fonctionnel (Block Diagram)

```
[Capteur Humidité DHT22] ──┐
[Capteur pH analogique]  ──┼──► [ESP32] ──► [Wi-Fi] ──► [RabbitMQ] ──► [Backend / ML]
[Capteur Lumière BH1750] ──┘
```

### Schéma électrique (Schematic)

> 📁 `schematics/schematic.png` *(à ajouter)*

## Composants

| Composant | Utilisation | Prix estimé |
|---|---|---|
| ESP32 DevKit V1 | Microcontrôleur principal — cerveau du dispositif, gère les capteurs et la communication Wi-Fi | 35 RON |
| Capteur DHT22 | Mesure de l'humidité relative de l'air (0–100%) et de la température | 18 RON |
| Capteur pH analogique (SEN0161) | Mesure du pH du sol via une sonde immergée dans le substrat | 65 RON |
| Capteur de lumière BH1750 | Mesure de l'intensité lumineuse ambiante en lux via I²C | 12 RON |
| Breadboard | Platine de prototypage sans soudure | 10 RON |
| Fils de connexion | Câblage des composants | 7 RON |
| Résistances (10kΩ) | Pull-up pour le bus I²C du BH1750 | 5 RON (set) |
| Câble USB micro | Alimentation et programmation de l'ESP32 | 8 RON |
| **Total estimé** | | **~160 RON** |

## Brochage (Pinout)

| Capteur | Broche capteur | Broche ESP32 |
|---|---|---|
| DHT22 | DATA | GPIO4 |
| DHT22 | VCC | 3.3V |
| DHT22 | GND | GND |
| BH1750 | SDA | GPIO21 |
| BH1750 | SCL | GPIO22 |
| BH1750 | VCC | 3.3V |
| BH1750 | GND | GND |
| Sonde pH | AOUT | GPIO34 (ADC) |
| Sonde pH | VCC | 5V |
| Sonde pH | GND | GND |

## Bibliothèques

| Bibliothèque | Description | Utilisation |
|---|---|---|
| `DHT.h` | Bibliothèque Adafruit pour les capteurs DHT | Lecture de la température et de l'humidité depuis le DHT22 |
| `BH1750.h` | Bibliothèque pour le capteur de lumière BH1750 | Lecture de la luminosité en lux via le bus I²C |
| `WiFi.h` | Bibliothèque standard ESP32 | Connexion au réseau Wi-Fi local |
| `PubSubClient.h` | Client MQTT pour Arduino/ESP32 | Envoi des données vers le broker (alternative légère à RabbitMQ direct) |
| `ArduinoJson.h` | Sérialisation JSON | Formatage des lectures capteurs en JSON avant envoi |

## Journal de bord (Log)

| Date | Entrée |
|---|---|
| — | Sélection des composants et commande du matériel |
| — | Câblage et test individuel de chaque capteur |
| — | Intégration ESP32 + envoi Wi-Fi vers RabbitMQ |
| — | Tests de terrain et calibration de la sonde pH |

## Liens de référence

- [Tutoriel : ESP32 avec DHT22 (Humidity & Temperature)](https://randomnerdtutorials.com/esp32-dht11-dht22-temperature-humidity-sensor-arduino-ide/)
- [Guide : Capteur de lumière BH1750 avec ESP32](https://randomnerdtutorials.com/esp32-bh1750-ambient-light-sensor/)
- [Guide : Capteur pH SEN0161 avec Arduino](https://wiki.dfrobot.com/PH_meter_SKU__SEN0161_)
- [Tutoriel : ESP32 envoi de données via Wi-Fi (HTTP POST)](https://randomnerdtutorials.com/esp32-http-post-ifttt-thingspeak-arduino/)
