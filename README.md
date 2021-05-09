# SimpleCaptcha
A stateless captcha bot

# What is this
This is a bot that, when added to your group as administrator, requires new users to complete a captcha before allowing them to chat.
Everything needed is saved in the buttons of the message encrypted with AES-IGE thus the only thing required is the .env file (which will be created when ran) since it contains the key.

# Setup
- Clone the repo
```bash
git clone https://github.com/GodSaveTheDoge/simpleCaptchaBot && cd simpleCaptchaBot
```
- Install dependencies
```bash
pip install -r requirements.txt
```
- Create a bot and get the token. Change the token in config.ini
- (Optional) Go to https://my.telegram.org/apps, create a new app and change api_id/api_hash in config.ini
- Download emojis (Note that this might take some time)
```bash
python get_emojis.py
#
# or
#
wget "https://github.com/GodSaveTheDoge/simpleCaptchaBot/releases/download/emoji-release/apple.zip" && \
mkdir -p resources/emojis && \
unzip apple.zip -d resources/emojis
```
- (Optional) Remove the backgrounds in resources/backgrounds and put your own
- Run it
```bash
python -m simpleCaptcha
```
