# face-autolock 🔒

**Your Windows laptop locks itself when you walk away.** That's it.

It watches your webcam, and only locks when you actually get up and leave. Looking down, turning your head or reading with your head bowed will **not** lock it.

## What it does, in plain words

| You do this | What happens |
|---|---|
| Sit in front of the laptop | Nothing |
| Look down, turn your head, lean to the side | Nothing |
| Get up and leave for 10 seconds | Windows locks |
| Come back | It re-arms itself |

Two safety rules:
- It starts working only **after it has seen a person**, so an empty room never triggers a lock.
- If the room is too dark to see, it **never locks**, because it can't tell.

## Setup (3 steps)

1. Install [Python](https://www.python.org/downloads/) and tick **"Add Python to PATH"** during installation.
2. Download this project, open a terminal in its folder and run:
   ```bash
   pip install -r requirements.txt
   ```
3. Test it with a preview window:
   ```bash
   python autolock.py --show
   ```
   You should see a blue box around your face and the text **ARMED**. Walk away for 10 seconds and your PC locks. Press `q` to quit.

When you're happy with it, run it without the window:
```bash
python autolock.py
```

## Settings

| Option | Default | What it does |
|---|---|---|
| `--away` | 10 | Seconds you must be gone before it locks |
| `--body-grace` | 60 | Seconds you still count as "here" if only your upper body is seen (head down, reading) |
| `--min-brightness` | 25 | Below this brightness (0-255) it is too dark to judge and never locks |
| `--camera` | 0 | Camera number, try 1 if you have more than one |
| `--show` | off | Show the preview window |

Example: `python autolock.py --away 15`

## Start it automatically with Windows

1. Press `Win + R`, type `shell:startup` and press Enter.
2. In that folder create `autolock.bat` with this content (change the path):
   ```bat
   @echo off
   pythonw "C:\path\to\autolock.py"
   ```

## How do I unlock it with my face?

Windows doesn't allow scripts to unlock the screen (that's a security rule). Use **Windows Hello** for that: Settings, Accounts, Sign-in options. This project **locks**, Windows Hello **unlocks**.

## Troubleshooting

- **"Could not open the camera"**: another app (Zoom, Teams, the Camera app) is using it. Close it, or try `--camera 1`.
- **It locks while I'm sitting there**: make the room brighter, face the camera, or raise `--away` to 15 or 20.
- **It never locks**: run with `--show`. If it says `WAITING FOR A HUMAN`, it hasn't seen you yet. A poster or photo of a face behind you can also keep it from locking.
- **`pip install` gives an OpenCV error**: this project needs OpenCV 4.x (OpenCV 5 removed the face detector it uses). `requirements.txt` already pins the right version.

## How it works

OpenCV Haar cascades look for a face (front and side) and an upper body, about twice per second. A small state machine decides when a person has really left. When they have, it calls the Windows `LockWorkStation` function once.

## Privacy

No picture is ever saved and nothing is sent over the internet. Everything runs on your laptop.

## Tests

The "has the person left?" logic is covered by unit tests:
```bash
python -m unittest discover tests
```

## License

MIT
