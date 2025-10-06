# 🤖 Resistor Code Bot - Universal Resistor Assistant

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

![Russian](https://img.shields.io/badge/Russian-Documentation-red)

# 🇷🇺 [Russian documentation available here](README.md)

Multifunctional Telegram bot to determine the values of resistors by color codes and SMD codes. Supports all popular types of resistors and marking formats.

## ✨ Features

### 🎨 Cylindrical Resistors

- **Value determination** based on color bands (4 and 5 bands)
- **Color code generation** from a given value
- **Simultaneous output** of both 4-band and 5-band markings
- **Russian names** of colors in responses

### 🔤 SMD Resistors

- **Decoding SMD codes** into resistance values
- **Generating SMD codes** from resistance values
- **Series support**: E24 (±5%), E96 (±1%)
- **Code formats**: 3-digit, 4-digit, R-format

### 🎯 Convenient Interface

- **Persistent keyboard** with quick access to all features
- **Automatic request type detection**
- **Contextual modes** for precise control
- **Detailed examples** and tips

## 🎯 Usage

### Main Commands

| Command  | Description                |
| -------- | -------------------------- |
| `/start` | Start working with the bot |
| `/help`  | Help using the bot         |

### Menu Buttons

The bot uses a persistent keyboard with 4 buttons:

```
[🎨 Cylindrical] [🔤 SMD Resistors]
[ℹ️ Help] [🏠 Main Menu]
```

### Example Queries

#### 🎨 Cylindrical Resistors

**Determination of value by colors:**

```
brown black red gold
```

_Answer: 1.00 kΩ ±5%_

**Getting marking by value:**

```
470 Ω
```

_Answer shows both markings:_

```
🎨 Color Markings:

4-band:
yellow → violet → brown → gold

5-band:
yellow → violet → black → black → brown
```

#### 🔤 SMD Resistors

**Decoding codes:**

```
103
```

_Answer: 10 kΩ (E24)_

```
4R7
```

_Answer: 4.7 Ω (R-format)_

```
01C
```

_Answer: 10 kΩ (E96)_

**Generation of codes:**

```
10k
```

_Answer:_

```
💎 Value: 10.00 kΩ
🔤 SMD Codes:
• 103 (E24)
• 01C (E96)
```

### Automatic Detection

The bot automatically detects your request type:

- **Colors** → displays value
- **Value** → displays color markings
- **SMD code** → displays value
- **Value in SMD mode** → displays SMD codes

## 🔧 Technical Details

### Supported Formats

#### Color Coding

- **4 bands**: digit, digit, multiplier, tolerance
- **5 bands**: digit, digit, digit, multiplier, tolerance

#### SMD Codes

| Type         | Format            | Example | Value   | Tolerance |
| ------------ | ----------------- | ------- | ------- | --------- |
| E24          | 3 digits          | `103`   | 10 kΩ   | ±5%       |
| E96          | 2 digits + letter | `01C`   | 10 kΩ   | ±1%       |
| R-format     | With letter R     | `4R7`   | 4.7 Ω   | -         |
| Small values | R + digits        | `R047`  | 0.047 Ω | -         |

### Color Encoding

| Color     | Digit | Multiplier    | Tolerance |
| --------- | ----- | ------------- | --------- |
| 🖤 Black  | 0     | 1             | -         |
| 🤎 Brown  | 1     | 10            | ±1%       |
| ❤️ Red    | 2     | 100           | ±2%       |
| 🧡 Orange | 3     | 1,000         | -         |
| 💛 Yellow | 4     | 10,000        | -         |
| 💚 Green  | 5     | 100,000       | ±0.5%     |
| 💙 Blue   | 6     | 1,000,000     | ±0.25%    |
| 💜 Violet | 7     | 10,000,000    | ±0.1%     |
| 🤍 Gray   | 8     | 100,000,000   | ±0.05%    |
| ⚪ White  | 9     | 1,000,000,000 | -         |
| 💛 Gold   | -     | 0.1           | ±5%       |
| ⚪ Silver | -     | 0.01          | ±10%      |

## 📊 Knowledge Base

### Standard Resistor Series

- **E24 (24 values)**: ±5% tolerance
- **E96 (96 values)**: ±1% tolerance
- **E12, E48, E192**: can be added if needed

### Common Values

| Value  | 4-band                  | 5-band                         | SMD Codes |
| ------ | ----------------------- | ------------------------------ | --------- |
| 10 Ω   | brown-black-black-gold  | brown-black-black-gold-brown   | 10R, 010  |
| 100 Ω  | brown-black-brown-gold  | brown-black-black-brown-brown  | 101, 01A  |
| 1 kΩ   | brown-black-red-gold    | brown-black-black-brown-brown  | 102, 01B  |
| 10 kΩ  | brown-black-orange-gold | brown-black-black-red-brown    | 103, 01C  |
| 100 kΩ | brown-black-yellow-gold | brown-black-black-orange-brown | 104, 01D  |

## 🚀 Quick Start

### Install Dependencies

```bash
# Clone repository
git clone https://github.com/cirodil/resistor_code_bot.git
cd resistor_code_bot

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Configure the Bot

1. **Create a bot** via [@BotFather](https://t.me/BotFather) in Telegram
2. **Get token** and create an `.env` file:

```env
BOT_TOKEN=your_telegram_bot_token_here
BOT_LOG_LEVEL=INFO  # optionally: DEBUG, INFO, WARNING, ERROR
```

3. **Run the bot**:

```bash
python resistor_code_bot.py
```

## 📁 Project Structure

```
resistor-bot/
├── resistor_code_bot.py          # Main bot file
├── resistor_data.py         # Color coding data
├── smd_decoder.py           # SMD decoder logic
├── .env                     # Environment variables (created)
├── .env.example             # Example env variables
├── requirements.txt         # Python dependencies
└── README.md               # This documentation
```

### Project Modules

- **`resistor_code_bot.py`** - main module with command handlers
- **`resistor_data.py`** - dictionaries of colors, multipliers, and tolerances
- **`smd_decoder.py`** - logic for handling SMD codes

## 🛠 Development

### Requirements

- Python 3.8+
- python-telegram-bot 20.7+
- python-dotenv 1.0+

### Local Development

```bash
# Installation in development mode
pip install -r requirements.txt

# Run the bot
python resistor_code_bot.py

# Test individual modules
python -c "from resistor_data import COLOR_CODES; print(COLOR_CODES['red'])"
python -c "from smd_decoder import smd_to_resistance; print(smd_to_resistance('103'))"
```

### Adding New Features

1. **New colors**: edit `resistor_data.py`
2. **New SMD codes**: edit `smd_decoder.py`
3. **New commands**: add handlers in `resistor_code_bot.py`

## 🐛 Troubleshooting

### Common Issues

**Bot doesn't start:**

- Check that you have created an `.env` file with the token
- Ensure all dependencies are installed
- Verify logs for errors

**Requests not recognized:**

- Use Russian color names
- Specify units for values: Ω, kΩ, MΩ
- SMD codes must be in correct format

**Errors in calculations:**

- Check the order of colors
- Make sure the value is within valid range

### Logging

Logging level can be configured through environment variable:

```env
BOT_LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

## 🤝 Contributing

We welcome contributions to this project!

1. Fork the repository
2. Create a branch for your feature (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Requirements

- Adhere to PEP8
- Documentation for new features
- Tests for new functionality
- Compatibility with existing API

## 📝 Roadmap

- [ ] Support for 6-band marking (temperature coefficient)
- [ ] Database of standard values
- [ ] Voltage divider calculator
- [ ] Capacitors and inductors support
- [ ] Web interface for advanced analysis
- [ ] API for integration with other applications
- [ ] User query history

## 📄 License

This project is licensed under the MIT license.

## 📞 Support

If you encounter issues or questions:

1. Check [Issues](https://github.com/cirodil/resistor-bot/issues) on GitHub
2. Create a new issue describing the problem
3. Contact via Telegram: [@kvgorodetsky](https://t.me/kvgorodetsky)

## 🙏 Acknowledgments

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - excellent library for Telegram bots
- Electronics community for testing and feedback
- Project contributors for ideas and improvements

---

**⭐ If you like the project, give it a star on GitHub!**

_Made with ❤️ for electronics enthusiasts and hobbyists_

_Last updated: October 2025_
