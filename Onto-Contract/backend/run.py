from app import create_app


app = create_app()


if __name__ == "__main__":
    config = app.config["APP_SETTINGS"]
    app.run(
        host=config["app"]["host"],
        port=config["app"]["port"],
        debug=config["app"]["debug"],
        threaded=True,
    )
