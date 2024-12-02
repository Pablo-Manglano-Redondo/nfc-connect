from app import app

if __name__ == "__main__":

    app.run(debug=True)
    # EN PROD:     app.run(host='0.0.0.0', port=5000, debug=False)
