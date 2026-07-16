from app.factory import AppFactory

app = AppFactory().create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
