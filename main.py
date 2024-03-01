import json
from flask import Flask, request, jsonify
import pandas as pd
import io
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import MultiLabelBinarizer
from joblib import load
import gc

app = Flask(__name__)
# Load the trained model
rf_classifier = load("./models/trained_model.joblib")

# Load the MultiLabelBinarizer instance
mlb = load("./models/mlb_model.joblib")


@app.route("/pre-defined", methods=["POST"])
def process_json():
    try:
        json_data = request.get_json()
        dataframe = pd.DataFrame(json_data)
        reports_wc, reports_cy, reports_ny = generate_individual_reports(dataframe)
        return jsonify(
            {
                "withered_reports": reports_wc,
                "crop_yield": reports_cy,
                "net_yield": reports_ny,
            }
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route("/suggested-tags", methods=["POST"])
def get_suggested_tags():
    try:
        json_data = request.get_json()
        new_samples = pd.DataFrame(json_data)

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
        suggested_tags = [
            [tag.strip() for tag in tags] for tags in predicted_tags_new_samples
        ]

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

        suggested_tags_with_desc = []
        # Iterate over each row in the DataFrame
        for i, row in new_samples.iterrows():
            desc_tags = []
            for tag in tags_to_check:
                if tag in suggested_tags[i]:
                    desc_tags.append(tag)
                    suggested_tags[i].remove(tag)
            suggested_tags_with_desc.append({"tags": suggested_tags[i]})

        return jsonify({"suggested_tags": suggested_tags_with_desc})
    except Exception as e:
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
    # Lists to store messages for each plant
    report_wc = []
    report_cy = []
    report_ny = []

    terrible_wc = "The withered crops have significantly impacted yield. Immediate action is needed, withered crops have significantly impacted yield."
    bad_wc = "The number of withered crops is concerning and impacting yield"
    good_wc = "The withered crops count is zero, indicating excellent crop health and minimal losses during cultivation. This suggests effective pest control, optimal water management, and overall favorable growing conditions. Keep up the good work!"
    mild_wc = "There are some losses due to withered crops, but they're manageable"

    excellent_cy = "Crop yield is exceptional!"
    bad_cy = "Crop yield is below expectations"
    average_cy = "crop yield is satisfactory"
    terrible_cy = "Crop yield is disastrously low"

    excellent_ny = "Net yield exceeds expectations"
    bad_ny = "Net yield is lower than anticipated"
    average_ny = "Net yield is performing average"
    terrible_ny = "Net yield is negative, indicating significant losses"

    for index, row in dataframe.iterrows():
        report = f"Report for {row['plant']} crop:\n"

        # Analyze withered crops
        if row["type"] == 1:
            if row["withered_crops"] >= 5:
                report += f"Withered crops have significantly impacted yield. Immediate action is needed. "
                report_wc.append((row["plant"] + ": " + terrible_wc))
            elif 0 < row["withered_crops"] < 5:
                report += (
                    f"The number of withered crops is concerning and impacting yield "
                )
                report_wc.append((row["plant"] + ": " + bad_wc))
            elif row["withered_crops"] == 0:
                report += f"The withered crops count is zero, indicating excellent crop health and minimal losses during cultivation. This suggests effective pest control, optimal water management, and overall favorable growing conditions. Keep up the good work! "
                report_wc.append((row["plant"] + ": " + good_wc))
            else:
                report += f"There are some losses due to withered crops, but they're manageable "
                report_wc.append(row["plant"] + ": " + mild_wc)
        elif row["type"] == 0:
            if row["withered_crops"] > 5:
                report += f"Withered crops have significantly impacted yield. Immediate action is needed. "
                report_wc.append((row["plant"] + ": " + terrible_wc))
            elif row["withered_crops"] >= 3:
                report += (
                    f"The number of withered crops is concerning and impacting yield "
                )
                report_wc.append((row["plant"] + ": " + bad_wc))
            elif 1 <= row["withered_crops"] < 3:
                report += f"There are some losses due to withered crops, but they're manageable "
                report_wc.append(row["plant"] + ": " + mild_wc)
            else:
                report_wc.append(row["plant"] + ": " + good_wc)

        # Analyze crop yield
        if row["crop_yield"] >= 5 and row["type"] == 1:
            report += f"  "
            report_cy.append((row["plant"] + ": " + average_cy))
        elif row["crop_yield"] < 5 and row["type"] == 1:
            report += f"crop yield is below expectations "
            report_cy.append((row["plant"] + ": " + bad_cy))
        elif row["crop_yield"] < 0 and row["type"] == 1:
            report += f"crop yield is disastrously low "
            report_cy.append((row["plant"] + ": " + terrible_cy))
        elif row["crop_yield"] >= 10 and row["type"] == 1:
            report += f"Crop yield is exceptional! "
            report_cy.append((row["plant"] + ": " + excellent_cy))

        # Analyze net yield
        if row["net_yield"] >= 12 and row["type"] == 1:
            report += f"net yield exceeds expectations.\n"
            report_ny.append((row["plant"] + ": " + excellent_ny))
        elif row["net_yield"] >= 8 and row["type"] == 1:
            report += f"net yield is performing average. \n"
            report_ny.append((row["plant"] + ": " + average_ny))
        elif row["net_yield"] < 8 and row["type"] == 1:
            report += f"net yield is below expectations\n"
            report_ny.append((row["plant"] + ": " + bad_ny))
        elif row["net_yield"] < 0 and row["type"] == 1:
            report += f"net yield is negative, indicating significant losses\n"
            report_ny.append((row["plant"] + ": " + terrible_ny))

        # type 0

        #  crop yield
        if row["crop_yield"] == 1 and row["type"] == 0:
            report += f"crop yield is satisfactory "
            report_cy.append(row["plant"] + ": " + average_cy)
        elif row["crop_yield"] < 1 and row["crop_yield"] > 0 and row["type"] == 0:
            report += f"Crop yield is below expectations, "
            report_cy.append(row["plant"] + ": " + bad_cy)
        elif row["crop_yield"] < 0 and row["type"] == 0:
            report += f"Crop yield is disastrously low, "
            report_cy.append(row["plant"] + ": " + terrible_cy)
        elif row["crop_yield"] > 1 and row["type"] == 0:
            report += f"Crop yield is exceptional! "
            report_cy.append(row["plant"] + ": " + excellent_cy)

        # net yield
        if row["net_yield"] == row["planted_qty"] and row["type"] == 0:
            report += f"net yield is performing average. \n"
            report_ny.append(average_ny)
        elif row["net_yield"] > row["planted_qty"] and row["type"] == 0:
            report += f"net yield exceeds expectationsyield is commendable. \n"
            report_ny.append(excellent_ny)
        elif row["net_yield"] < row["planted_qty"] and row["type"] == 0:
            report += f"net yield is lower than anticipated\n"
            report_ny.append(bad_ny)
        elif row["net_yield"] < 0 and row["type"] == 0:
            report += f"net yield is negative, indicating significant losses\n"
            report_ny.append(terrible_ny)

    return report_wc, report_cy, report_ny


if __name__ == "__main__":
    app.run(host="0.0.0.0")
