# Acquire

<img src="acquire_boxart_glitching.png" alt="Project Cover Image" width=35% height=35%>

Digital remaster of the 1964 board game *Acquire*, originally published by 3M. Written in Python.

## To Run

Install Python 3.12.7 @ <https://www.python.org/downloads/release/python-3127/>

Install Required Packages: `pip install -r requirements.txt`

Run: `python main.py`

## To Build (using PyInstaller)

Install PyInstaller: `pip install pyinstaller`

Run: `pyinstaller build.spec`

The .exe file can be found in: `.\dist`

## Server Hosting

To run a server accessible from outside of its local network (LAN), the Host is required to Port Forward their hosting device to the open internet. This is an advanced task that differs based on the Host's network situation and router, so I cannot explain how to do this here. Look it up or ask your go-to tech person for help. All Acquire server/client communication occurs over port `30545`.
