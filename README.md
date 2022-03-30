# Snooker 3D simulation in Python 

**Snooker** is a simple game that was programmed in Python using the [HARFANG 3D framework](https://www.harfang3d.com).

*This project implements the simplest possible gameplay loop, relying on the Bullet physics engine for the most complex part of the simulation. This project can be used as a basis for the development of a more complex gameplay, or for AI training by plugging directly into the code that manages the game interactions.*

![Snooker Banner](https://github.com/harfang3d/snooker-python-hg2/raw/main/screenshots/scene0.png)

## How to run the Snooker ?

### The easy way

1. Download the [Windows release](https://github.com/harfang3d/snooker-python-hg2/releases) (Snooker.Release.HG.3.2.0.zip)
2. Unzip it in a local folder
3. Double click on `2-start_game.bat` if you run the game on a low-end machine
4. Double click on `2bis-start_game - AAA quality.bat` if you run the game on a high-end machine with a discrete GPU (GeForce GTX850 or above)

### Using your own Python interpreter
1. Get [Python 3](https://www.python.org/downloads/)
1. Get HARFANG 3D
	1. Either download it from the [HARFANG website](https://www.harfang3d.com/releases/3.2.0/) and follow the [install instructions](https://www.harfang3d.com/docs/3.2.0/man.cpython/)
	1. Or, using PIP in the command line, type '*pip install -Iv harfang==3.2.0*'
1. Clone/download this repository
1. run *python main.py* to launch the game
1. run *python main.py --aaa* to launch the game with AAA quality

## How to play ?
1. Click on one of the 3 balls with the `left mouse button`.
1. Aim by moving the mouse on the `horizontal axis`.
1. Shoot with the `left mouse button`.
1. To reset the game, press the `right mouse button`.
1. Press `ESC` to quit.

## Credits
* Python programming : Eric Kernin
* Release : Clément Beudot

## Screenshots
![Screenshot 1](https://github.com/harfang3d/snooker-python-hg2/raw/main/screenshots/scene1.png)
![Screenshot 2](https://github.com/harfang3d/snooker-python-hg2/raw/main/screenshots/scene2.png)
