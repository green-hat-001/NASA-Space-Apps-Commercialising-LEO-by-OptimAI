# trigger.py
from flask import Flask, render_template, request
import subprocess

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    message = ""
    if request.method == "POST":
        # Get input from form
        input_value = request.form.get("input_value", "default")

        with open("config.txt", "w") as f:
           f.write(str(input_value))  # convert to string

        print("Config saved!")
        
        # Run app.py and wait for it to finish
        result = subprocess.run(["python3", "app.py", input_value], capture_output=True, text=True)
        
        print(input_value)

    return render_template("index.html", message=message)

if __name__ == "__main__":
    app.run(debug=True)
