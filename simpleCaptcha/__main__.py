from pathlib import Path

from pyrogram import Client

Client(
    ":memory:",
    config_file="config.ini",
    plugins=dict(
        root=str((Path(__file__).parent / "plugins").relative_to(Path(".").resolve()))
    ),
).run()
