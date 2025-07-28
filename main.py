from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from openai import OpenAI
from prompts import PROMPTS
from dotenv import load_dotenv
import traceback

# .env laden
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Nieuwe client aanmaken
client = OpenAI(api_key=api_key)

app = Flask(__name__)
CORS(app)

@app.route("/check", methods=["POST"])
def check():
    try:
        data = request.get_json()
        text = data["text"]
        preset = data["preset"]

        system_prompt = PROMPTS.get(preset, PROMPTS["web"])

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.2
        )

        reply = response.choices[0].message.content

        comments = [c.strip("- ").strip() for c in reply.split("\n") if c.strip().startswith("- ")]
        return jsonify({"comments": comments})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/suggest", methods=["POST"])
def suggest():
    try:
        data = request.get_json()
        comment = data["comment"]
        preset = data["preset"]

        system_prompt = "Je bent een hulpvaardige redacteur. Geef alleen een verbeterde versie van de geciteerde zin in de opmerking, zonder verdere uitleg. Houd rekening met de stijl die hoort bij het preset-type."

        user_prompt = f"""
Preset: {preset}
Opmerking: {comment}
"""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2
        )

        suggestion = response.choices[0].message.content.strip()
        return jsonify({"suggestion": suggestion})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    
@app.route("/styleguide", methods=["POST"])
def styleguide():
    try:
        data = request.get_json()
        preset = data.get("preset", "web")

        full_prompt = PROMPTS.get(preset, "")
        if not full_prompt:
            return jsonify({"styleguide": "Geen stijlregels gevonden."})

        # Alleen het stuk vanaf "Stijlregels:" tot de volgende dubbele newline
        if "Stijlregels:" in full_prompt:
            regels = full_prompt.split("Stijlregels:")[1].strip()
            regels = regels.split("\n\n")[0].strip()
        else:
            regels = "Geen stijlregels gevonden."

        return jsonify({"styleguide": regels})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))  # Render geeft dynamisch een poort door
    app.run(host='0.0.0.0', port=port)
