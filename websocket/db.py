# app/db.py

from tortoise.contrib.fastapi import register_tortoise

TORTOISE_ORM = {
    "connections": {
        "default": "mysql://root@localhost:3306/vihaan"
        # example: "mysql://root:password@localhost:3306/mydatabase"
    },
    "apps": {
        "models": {
            "models": ["websocket.models"],  # your app models module
            "default_connection": "default",
        }
    }
}

def init_db(app):
    register_tortoise(
        app,
        config=TORTOISE_ORM,
        generate_schemas=True,
        add_exception_handlers=True,
    )
