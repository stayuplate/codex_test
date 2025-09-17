
<p align="center">
    <img src="https://img.shields.io/badge/engine-alpha-blueviolet?style=for-the-badge" alt="Engine Status"/>
    <img src="https://img.shields.io/badge/python-3.8%2B-green?style=for-the-badge" alt="Python Version"/>
    <img src="https://img.shields.io/badge/license-MIT-yellow?style=for-the-badge" alt="License"/>
</p>

<h1 align="center">🎮 Game Engine</h1>

<p align="center">
    <b>Leichtgewichtig. Modular. Spaßig.</b><br>
    <i>Baue kleine Spiele mit großer Wirkung!</i>
</p>

---

Willkommen im Game Engine Repository!<br>
Dieses Projekt ist ein laufender Versuch, eine leichtgewichtige und dennoch robuste Game Engine für einfache, spaßige Spiele zu bauen. Egal ob Einsteiger oder erfahrener Entwickler – hier kannst du loslegen!

---

## ✨ Features


Diese Engine befindet sich in Entwicklung, aber das erwartet dich (oder ist geplant):


| 🌍 Plattformen | 🖼️ 2D Assets | 🎹 Audio | ⚡ Events | 🧲 Physik | 🗺️ Szenen | 🔌 Erweiterbar |
|:-------------:|:------------:|:--------:|:--------:|:---------:|:--------:|:--------------:|
| ✔️            | ✔️           | ✔️       | ✔️       | ✔️        | ✔️       | ✔️             |

<details>
<summary>Geplante Features</summary>

- Cross-platform support
- 2D Asset Management
- Event System
- Physics Engine
- Audio System
- Scene Management
- Extensible
</details>


<sub><i>Hinweis: Viele Features sind noch in Arbeit!</i></sub>

---

## 🚀 Schnellstart

### Voraussetzungen


* Python 3.8+
* (Optional) C++ Compiler & CMake für native Module
* Siehe weitere Abhängigkeiten in den jeweiligen Modulen

git clone https://github.com/your_username/game-engine.git

### Installation

```bash
git clone https://github.com/your_username/game-engine.git
cd game-engine
```

### Engine bauen (optional)
```bash
mkdir build
cd build
cmake ..
make
```

### Beispiel ausführen
```bash
python examples/first_game.py
```


---

## 🕹️ Eigene Spiele erstellen

1. **Umgebung aufsetzen:** Erweitere die Basisklassen (`GameApp`, `Scene` etc.) für dein Spiel.
2. **Gameplay designen:** Füge Objekte und Logik mit den Modulsystemen hinzu (Physik, Rendering, Audio ...).
3. **Testen & Spaß haben:** Starte dein Spiel und bring deine Ideen zum Leben!

👉 Ausführliche Anleitungen folgen bald unter `/docs` und `/examples`.

---

## 🧩 Beispiel: Hello, Game World!

```cpp
#include "GameEngine.h"

class MyGame : public GameApp {
public:
    void OnStart() override {
        // Initialize game objects, load assets, etc.
        AddGameObject(new Player());
    }
    void OnUpdate(float deltaTime) override {
        // Update game logic here.
    }
    void OnRender() override {
        DrawText(100, 100, "Hello, Game World!");
    }
};

int main() {
    MyGame game;
    game.Run();
    return 0;
}
```


---

## 🕵️‍♂️ Playable Demos

| Demo | Beschreibung |
|------|--------------|
| `examples/first_game.py` | 🟦 **Crystal Collector**<br>Ein Grid-Abenteuer: Sammle Kristalle, meide Gefahren! |
| `examples/lantern_maze.py` | 🟡 **Lantern Maze**<br>Nebellabyrinth: Fange Lichter, finde den Ausgang! |

Starte ein Demo mit:
```bash
python examples/first_game.py
```

game-engine/

---

## 🗂️ Projektstruktur

```plaintext
game-engine/
│
├── src/         # Engine-Quellcode
├── examples/    # Beispielspiele
├── assets/      # Gemeinsame Assets
├── docs/        # Dokumentation
├── tests/       # Tests
├── build/       # Build-Output (ignored)
└── README.md    # Übersicht
```


---

## 🤝 Mitmachen

Wir freuen uns über jeden Beitrag!<br>
**So kannst du helfen:**

- Fehler melden (Issues)
- Feature-Wünsche äußern (Discussions/Issues)
- Pull Requests einreichen (Bugfixes, Features, Optimierungen)

Bitte lies vorher die Contributing Guidelines und halte dich an den Code of Conduct.

---

## 🛣️ Roadmap

- Sprite-Rendering
- Eventgesteuerte Eingabe
- Physik-Engine (Kollisionen, Gravitation)
- UI-Framework (Buttons, Labels ...)
- Externe Assets laden (JSON, Tiled ...)
- Mehr Doku & Community


---

## 📝 Lizenz

MIT – frei für private & kommerzielle Nutzung.

---

## 💬 Support

Fragen? Probleme?<br>
Öffne ein Issue, poste in Discussions oder kontaktiere uns direkt.

---

<p align="center">
    <b>Happy coding! 🎮<br>Let’s make some amazing games together.</b>
</p>
