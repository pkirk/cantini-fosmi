<<<<<<< HEAD
# cantini-fosmi
=======
# Fantini Cosmi ECOCOMFORT 2 Smart VMC Controller

```
  ____            _   _       _   _____                   _ 
 / ___|__ _ _ __ | |_(_)_ __ (_) |  ___|__  ___ _ __ ___ (_)
| |   / _` | '_ \| __| | '_ \| | | |_ / _ \/ __| '_ ` _ \| |
| |__| (_| | | | | |_| | | | | | |  _| (_) \__ \ | | | | | |
 \____\__,_|_| |_|\__|_|_| |_|_| |_|  \___/|___/_| |_| |_|_|
                                               
```

This repository contains a Python program to control the Fantini Cosmi ECOCOMFORT 2 Smart VMC. It was developed by reverse-engineering the official APK due to the poor performance of the official app, which often fails with "No Connection" errors on iOS.

## Features

- Authenticate and manage tokens for secure communication.
- Retrieve and manage houses and devices.
- Send speed control commands to devices.
- Compute CRC checksums for communication integrity.

## Why This Exists

The official app is outdated and unreliable. This project aims to provide a better alternative and, in the near future, evolve into a Python library for integration with Home Assistant.

## Requirements

- Python 3.7+
- `requests` library
- `python-dotenv` for environment variable management

## Setup

1. Clone the repository.
2. Create a `.env` file with your Fantini Cosmi credentials:
   ```
   LOGIN=your_login
   PASSWORD=your_password
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run the script:
   ```
   python fantini.py
   ```

## Future Plans

- Refactor into a Python library.
- Add Home Assistant integration.

## Disclaimer

This project is not affiliated with or endorsed by Fantini Cosmi. Use at your own risk.
>>>>>>> 58b28de (Frist commitcommit)
