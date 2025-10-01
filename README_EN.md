```markdown
[file name]: README_EN.md

[file content begin]

# 🤖 Resistor Code Bot - Universal Resistor Assistant

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

A multifunctional Telegram bot for determining resistor values from color codes and SMD markings. Supports all popular resistor types and marking formats.

## ✨ Features

### 🎨 Cylindrical Resistors

- **Value determination** from color bands (4 and 5 bands)
- **Color code generation** from specified resistance value
- **Simultaneous display** of 4-band and 5-band color codes
- **Russian color names** in responses

### 🔤 SMD Resistors

- **SMD code decoding** to resistance values
- **SMD code generation** from resistance value
- **Supported series**: E24 (±5%), E96 (±1%)
- **Code formats**: 3-digit, 4-digit, R-format

### 🎯 User-Friendly Interface

- **Persistent keyboard** with quick access to all functions
- **Automatic query type detection**
- **Contextual modes** for precise control
- **Detailed examples** and hints

## 🎯 Usage

### Basic Commands

| Command  | Description                |
| -------- | -------------------------- |
| `/start` | Start working with the bot |
| `/help`  | Usage help                 |

### Menu Buttons

The bot uses a persistent keyboard with 4 buttons:
```

[🎨 Cylindrical] [🔤 SMD Resistors]
[ℹ️ Help] [🏠 Main Menu]

```

### Query Examples

#### 🎨 Cylindrical Resistors

**Value determination from colors:**

```

коричневый черный красный золотой

```

*Response: 1.00 kΩ ±5%*

**Get color codes from value:**

```

470 Ом

```

*Response shows both codings:*

```

🎨 Color codes:

4-band:
yellow → purple → brown → gold

5-band:
yellow → purple → black → black → brown

```

#### 🔤 SMD Resistors

**Code decoding:**

```

103

```

*Response: 10 kΩ (E24)*

```

4R7

```

*Response: 4.7 Ω (R-format)*

```

01C

```

*Response: 10 kΩ (E96)*

**Code generation:**

```

10к

```

*Response:*

```

💎 Value: 10.00 kΩ
🔤 SMD codes:
• 103 (E24)
• 01C (E96)

````

### Automatic Detection

The bot automatically detects your query type:

- **Colors** → shows resistance value
- **Resistance value** → shows color codes
- **SMD code** → shows resistance value
- **Resistance value in SMD mode** → shows SMD codes

## 🔧 Technical Details

### Supported Formats

#### Color Coding

- **4 bands**: digit, digit, multiplier, tolerance
- **5 bands**: digit, digit, digit, multiplier, tolerance

#### SMD Codes

| Type         | Format           | Example | Value    | Tolerance |
| ------------ | ---------------- | ------- | -------- | --------- |
| E24          | 3 digits         | `103`   | 10 kΩ    | ±5%       |
| E96          | 2 digits + letter | `01C`   | 10 kΩ    | ±1%       |
| R-format     | With letter R    | `4R7`   | 4.7 Ω    | -         |
| Small values | R + digits       | `R047`  | 0.047 Ω  | -         |

### Color Coding

| Color           | Digit | Multiplier     | Tolerance |
| --------------- | ----- | -------------- | --------- |
| 🖤 Black        | 0     | 1              | -         |
| 🤎 Brown        | 1     | 10             | ±1%       |
| ❤️ Red          | 2     | 100            | ±2%       |
| 🧡 Orange       | 3     | 1,000          | -         |
| 💛 Yellow       | 4     | 10,000         | -         |
| 💚 Green        | 5     | 100,000        | ±0.5%     |
| 💙 Blue         | 6     | 1,000,000      | ±0.25%    |
| 💜 Purple       | 7     | 10,000,000     | ±0.1%     |
| 🤍 Gray         | 8     | 100,000,000    | ±0.05%    |
| ⚪ White        | 9     | 1,000,000,000  | -         |
| 💛 Gold         | -     | 0.1            | ±5%       |
| ⚪ Silver       | -     | 0.01           | ±10%      |

## 📊 Knowledge Base

### Standard Resistor Series

- **E24 (24 values)**: ±5% tolerance
- **E96 (96 values)**: ±1% tolerance
- **E12, E48, E192**: can be added if needed

### Frequently Used Values

| Value  | 4-band                               | 5-band                                         | SMD Codes |
| ------ | ------------------------------------ | ---------------------------------------------- | --------- |
| 10 Ω   | brown-black-black-gold               | brown-black-black-gold-brown                   | 10R, 010  |
| 100 Ω  | brown-black-brown-gold               | brown-black-black-brown-brown                  | 101, 01A  |
| 1 kΩ   | brown-black-red-gold                 | brown-black-black-brown-brown                  | 102, 01B  |
| 10 kΩ  | brown-black-orange-gold              | brown-black-black-red-brown                    | 103, 01C  |
| 100 kΩ | brown-black-yellow-gold              | brown-black-black-orange-brown                 | 104, 01D  |

## 🚀 Quick Start

### Installing Dependencies

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
````

### Bot Setup

1. **Create a bot** via [@BotFather](https://t.me/BotFather) on Telegram
2. **Get the token** and create `.env` file:

```env
BOT_TOKEN=your_telegram_bot_token_here
BOT_LOG_LEVEL=INFO  # optional: DEBUG, INFO, WARNING, ERROR
```

3. **Start the bot**:

```bash
python resistor_code_bot.py
```

## 📁 Project Structure

```
resistor-bot/
├── resistor_code_bot.py          # Main bot file
├── resistor_data.py         # Color coding data
├── smd_decoder.py           # SMD resistor decoder
├── .env                     # Environment variables (created)
├── .env.example             # Environment variables example
├── requirements.txt         # Python dependencies
└── README_EN.md            # This documentation
```

### Project Modules

- **`resistor_code_bot.py`** - main bot module with command handlers
- **`resistor_data.py`** - color, multiplier and tolerance dictionaries
- **`smd_decoder.py`** - SMD code processing logic

## 🛠 Development

### Requirements

- Python 3.8+
- python-telegram-bot 20.7+
- python-dotenv 1.0+

### Local Development

```bash
# Install in development mode
pip install -r requirements.txt

# Start the bot
python resistor_code_bot.py

# Test individual modules
python -c "from resistor_data import COLOR_CODES; print(COLOR_CODES['красный'])"
python -c "from smd_decoder import smd_to_resistance; print(smd_to_resistance('103'))"
```

### Adding New Features

1. **New colors**: edit `resistor_data.py`
2. **New SMD codes**: edit `smd_decoder.py`
3. **New commands**: add handlers in `resistor_code_bot.py`

## 🐛 Troubleshooting

### Common Issues

**Bot won't start:**

- Check for `.env` file with token
- Make sure all dependencies are installed
- Check logs for errors

**Queries not recognized:**

- Use Russian color names
- Specify units for values: Ω, kΩ, MΩ
- SMD codes must be in correct format

**Calculation errors:**

- Check color order correctness
- Ensure value is within acceptable range

### Logging

Logging level can be configured via environment variable:

```env
BOT_LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

## 🤝 Contributing

We welcome contributions to the project!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Requirements

- PEP8 compliance
- Documentation for new functions
- Tests for new functionality
- Compatibility with existing API

## 📝 Development Roadmap

- [ ] 6-band color code support (temperature coefficient)
- [ ] Standard values database
- [ ] Voltage divider calculator
- [ ] Capacitor and inductor support
- [ ] Web interface for advanced analysis
- [ ] API for integration with other applications
- [ ] Multi-language support
- [ ] User query history

## 📄 License

This project is distributed under the MIT License.

## 📞 Support

If you encounter problems or have questions:

1. Check [Issues](https://github.com/cirodil/resistor-bot/issues) on GitHub
2. Create a new Issue with problem description
3. Contact on Telegram: [@kvgorodetsky](https://t.me/kvgorodetsky)

## 🙏 Acknowledgments

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - excellent Telegram bot library
- Electronics community for testing and feedback
- Project contributors for ideas and improvements

---

**⭐ If you like the project, give it a star on GitHub!**

_Made with ❤️ for the electronics and radio enthusiasts community_

_Updated: October 2025_
[file content end]

```

```
