# api.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from workflow import run_workflow, FarmerState

app = Flask(__name__)
CORS(app) 

@app.route("/api/recommend", methods=["POST"])
def get_recommendations():
    try:
        data = request.get_json()

        initial_state: FarmerState = {
            "profile": data.get("profile", {}),
            "schemes": [],
            "recommendations": None,
            "refinement_needed": False,
            "feedback": None,
            "visuals": []
        }

        result = run_workflow(initial_state)

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
