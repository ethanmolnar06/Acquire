# Acquire

<img src="assets/acquire_boxart_glitching.png" alt="Project Cover Image" width=35% height=35%>

Digital remaster of the 1964 board game *Acquire*, originally published by 3M. Written in Python.

## To Run From Aqcuire.exe

Install Python 3.12.7 @ <https://www.python.org/downloads/release/python-3127/>

Run: `Aqcuire.exe`

## To Run From Source

Install Python 3.12.7 @ <https://www.python.org/downloads/release/python-3127/>

Install Required Packages: `pip install .`

Run: `python src/main.py`

## To Build From Source (using PyInstaller)

### NOTE: Built Aqcuire.exe file still requires Python 3.12.7 installed, but does not require independent package installation

Install PyInstaller: `pip install .[build-exe]`

Run: `pyinstaller build.spec`

The .exe file can be found in: `.\dist`

## Server Hosting

To run a server accessible from outside of its local network (LAN), the Host is required to Port Forward their hosting device to the open internet. This is an advanced task that differs based on the Host's network situation and router, so I cannot explain how to do this here. Look it up or ask your go-to tech person for help. All Acquire server/client communication occurs over port `30545`.
