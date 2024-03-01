import json
from flask import Flask, request, jsonify
import pandas as pd
import io
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import MultiLabelBinarizer
from joblib import load
import gc

app = Flask(__name__)

@app.route('/pre-defined', methods=['POST'])
def process_json():
    try:

        json_data = request.get_json()

        # Convert json_data to a JSON-formatted string


        reports_wc, reports_cy, reports_ny = generate_individual_reports(df)

        return jsonify({"withered_reports": reports_wc, "crop_yield": reports_cy, "net_yield":  reports_ny})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route('/suggested-tags', methods=['POST'])
def get_suggested_tags():
    try:
        json_data = request.get_json()
        # Load the trained model
        rf_classifier = load("./models/trained_model.joblib")

        # Load the MultiLabelBinarizer instance
        mlb = load("./models/mlb_model.joblib")

        # Load new samples without tags

        json_data_string = json.dumps(json_data)
        new_samples = pd.read_json(io.StringIO(json_data_string[1:-1]), orient='records', lines=True)

        # Preprocess the new samples (similar to training data preprocessing)
        new_samples_features = new_samples[
            [
                "withered_crops",
                "crop_yield",
                "net_yield",
                "type",
            ]
        ]

        # Make predictions
        new_samples_predictions = rf_classifier.predict(new_samples_features)

        # Inverse transform predictions
        predicted_tags_new_samples = mlb.inverse_transform(new_samples_predictions)

        # Convert the list of tuples into a list of lists with removed spaces
        suggested_tags = [[tag.strip() for tag in tags] for tags in predicted_tags_new_samples]

        # Define the tags to check for in the suggested tags
        tags_to_check = [
            "commendable crop yield",
            "good crop yield",
            "average crop yield",
            "needs improvement",
            "terrible crop yield",
            "average crop yield",
            "commendable crop yield",
            "needs crop improvement",
            "terrible crop yield",
            "excellent net yield",
            "good net yield",
            "bad net yield",
            "good net yield",
            "excellent net yield",
            "bad net yield",
        ]

        desc_tags = []
        # Iterate over each row in the DataFrame
        for i, row in new_samples.iterrows():
            for tag in tags_to_check:
                if tag in suggested_tags[i]:
                    desc_tags.append(tag)
                    suggested_tags[i].remove(tag)
            new_samples.at[i, "tags"] = ", ".join(suggested_tags[i])
            new_samples.at[i, "desc"] = ", ".join(desc_tags)
        gc.collect()
        return jsonify({"tags": suggested_tags})
    except Exception as e:
        gc.collect()
        return jsonify({"status": "error", "message": str(e)})


@app.route("/growth-rate", methods=["POST"])
def compare_growth():
    try:
        data = request.get_json()
        average_growth = data.get("average_growth")
        recent_growth = data.get("recent_growth")

        if average_growth is None or recent_growth is None:
            return jsonify({"error": "Missing data"}), 400

        # values
        result = compare_growth(average_growth, recent_growth)

        return jsonify({"result": result})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def calculate_percentage_increase(average_growth, recent_growth):
    if average_growth == 0:
        return "No significant increase in growth rate."

    percentage_increase = ((recent_growth - average_growth) / abs(average_growth)) * 100
    return percentage_increase


# messasges pati conditions
def compare_growth(average_growth, recent_growth):
    if recent_growth > average_growth:
        percentage_increase = calculate_percentage_increase(
            average_growth, recent_growth
        )
        return f"You're doing well! Recent plant growth is higher than average growth by {percentage_increase:.2f}%."
    elif recent_growth < average_growth:
        return f"Your plant has a lower growth rate that is lower than your usual {average_growth:.2f}%."
    else:
        return "No significant increase in growth rate."



def generate_individual_reports(dataframe):
    # lists to store messages for each plant
    report_wc = []
    report_cy = []
    report_ny = []

    # strings
    terrible_wc = "Withered crops are too high"
    bad_wc = "Withered crops are at a concerning level"
    good_wc = "Withered crops are within acceptable limits"
    mild_wc = "Withered crops are mild. Needs improvement."

    excellent_cy = "Crop yield is commendable"
    bad_cy = "Crop yield is low"
    average_cy = "Crop yield is average"
    terrible_cy = "Crop yield is terrible"

    excellent_ny = "Net yield is commendable"
    bad_ny = "Net yield is below expectations"
    average_ny = "Net yield is average"
    
    for index, row in dataframe.iterrows():
        report = f"Report for {row['plant']} crop:\n"

        # Analyze withered crops
        if row["withered_crops"] > 5 and row["type"] == 1:
            report += f"Withered crops are too high, "
            report_wc.append((row["plant"] + ": " + terrible_wc))
        elif row["withered_crops"] >= 3 and row["type"] == 1:
            report += f"Withered crops are at a concerning level, "
            report_wc.append((row["plant"] + ": " + bad_wc))
        else:
            report += f"Withered crops are within acceptable limits, "
            report_wc.append((row["plant"] + ": " + good_wc))

        # Analyze crop yield
        if row["crop_yield"] >= 5 and row["type"] == 1:
            report += f"crop yield is average, "
            report_cy.append((row["plant"] + ": " + average_cy))
        elif row["crop_yield"] < 5 and row["type"] == 1:
            report += f"crop yield is low, "
            report_cy.append((row["plant"] + ": " + bad_cy))
        elif row["crop_yield"] < 0 and row["type"] == 1:
            report += f"crop yield is terrible, "
            report_cy.append((row["plant"] + ": " + terrible_cy))
        elif row["crop_yield"] >= 10 and row["type"] == 1:
            report += f"crop yield is commendable, "
            report_cy.append((row["plant"] + ": " + excellent_cy))

        # Analyze net yield
        if row["net_yield"] >= 12 and row["type"] == 1:
            report += f"net yield is commendable.\n"
            report_ny.append((row["plant"] + ": " + excellent_ny))
        elif row["net_yield"] >= 8 and row["type"] == 1:
            report += f"net yield is average. \n"
            report_ny.append((row["plant"] + ": " + average_ny))
        elif row["net_yield"] < 8 and row["type"] == 1:
            report += f"net yield is below expectations\n"
            report_ny.append((row["plant"] + ": " + bad_ny))

    return report_wc, report_cy, report_ny



if __name__ == '__main__':
    app.run(host='0.0.0.0')




