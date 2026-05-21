import pandas as pd
import glob
import os
import re
import time
import subprocess
from datetime import datetime
from sambanova import SambaNova

# ==============================
# CREATE OUTPUT FOLDER
# ==============================

os.makedirs("output", exist_ok=True)

# ==============================
# ABSOLUTE PATHS
# ==============================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATA_FOLDER = os.path.join(
    BASE_DIR,
    "data"
)

OUTPUT_FOLDER = os.path.join(
    BASE_DIR,
    "output"
)

print("📂 DATA FOLDER:")
print(DATA_FOLDER)

# ==============================
# PICK LATEST EXCEL FILE
# ==============================

files = glob.glob(
    os.path.join(
        DATA_FOLDER,
        "Early_Warning_Report*.xlsx"
    )
)

print("📄 FILES FOUND:")
print(files)

if len(files) == 0:

    raise FileNotFoundError(
        f"❌ No Excel files found inside:\n{DATA_FOLDER}"
    )

# ==============================
# EXTRACT DATE
# ==============================

def extract_date(file):

    filename = os.path.basename(file)

    match = re.search(
        r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-\d{2}',
        filename,
        re.IGNORECASE
    )

    return (
        datetime.strptime(
            match.group(0),
            "%b-%y"
        )
        if match else datetime.min
    )

latest_file = max(files, key=extract_date)

month_name = extract_date(
    latest_file
).strftime("%b-%y")

current_dt = datetime.strptime(
    month_name,
    "%b-%y"
)

prev_dt = (
    current_dt.replace(day=1)
    - pd.DateOffset(months=1)
).to_pydatetime()

prev_month_name = prev_dt.strftime("%b-%y")

print(f"\n📂 Processing File: {latest_file}")
print(f"📅 Current Month: {month_name}")

# ==============================
# LOAD EXCEL
# ==============================

df = pd.read_excel(latest_file)

df.columns = df.columns.str.strip()

df.rename(
    columns={
        'Employee Code': 'Employee ID'
    },
    inplace=True
)

df = df.loc[:, ~df.columns.duplicated()]

print("\n✅ DATA LOADED")

# ==============================
# COLUMN DETECTION
# ==============================

def find_col(keywords):

    for col in df.columns:

        if any(
            k.lower() in col.lower()
            for k in keywords
        ):
            return col

    return None

col_map = {

    "incentive": find_col(["incentive"]),

    "discount": find_col(["discount"]),

    "coverage": find_col(["coverage"]),

    "compliance": find_col(["compliance"]),

    "budget": find_col(
        ["month budget", "stretch"]
    ),

    "stock": find_col(["stock"]),

    "wap": find_col(["wap"]),

    "visit": find_col(
        ["manager visits"]
    )
}

print("\n📌 DETECTED COLUMNS:")
print(col_map)

# ==============================
# REMOVE VACANT
# ==============================

df['Is_Vacant'] = (
    df['Employee ID'].isin([0, '0'])
)

active_df = df[
    ~df['Is_Vacant']
].copy()

# ==============================
# SAFE CALC
# ==============================

def safe_calc(df, col, condition):

    if col:

        return condition(
            df[col]
        ).astype(int)

    return 0

# ==============================
# EWS LOGIC SWITCH
# ==============================

USE_REPORT_SCORE = True

# =====================================================
# OPTION 1 → REPORT SCORE
# =====================================================

if USE_REPORT_SCORE:

    print("\n✅ Using Report Score")

    # ==============================
    # CLEAN SCORE
    # ==============================

    active_df['EWS_Score'] = pd.to_numeric(
        active_df['Count of Red Flags'],
        errors='coerce'
    ).fillna(0)

    # ==============================
    # CLEAN CATEGORY
    # ==============================

    active_df['Category'] = (
        active_df['Category']
        .astype(str)
        .str.strip()
        .str.lower()
    )

    # ==============================
    # STANDARDIZE RISK LEVEL
    # ==============================

    def clean_risk(x):

        if "high" in x:
            return "High Risk"

        elif "medium" in x:
            return "Medium Risk"

        elif "low" in x:
            return "Low Risk"

        else:
            return "Low Risk"

    active_df['Risk_Level'] = (
        active_df['Category']
        .apply(clean_risk)
    )

    # ==============================
    # DEBUG PRINT
    # ==============================

    print("\n📌 RISK LEVEL COUNTS:")
    print(
        active_df['Risk_Level']
        .value_counts()
    )

# =====================================================
# OPTION 2 → OLD PYTHON LOGIC
# =====================================================

else:

    print("\n✅ Using Python Scoring Logic")

    active_df['EWS_Score'] = (

        safe_calc(
            active_df,
            col_map['incentive'],
            lambda x: x >= 12000
        )

        +

        safe_calc(
            active_df,
            col_map['discount'],
            lambda x: x > 0.25
        )

        +

        safe_calc(
            active_df,
            col_map['coverage'],
            lambda x: x < 0.7
        )

        +

        safe_calc(
            active_df,
            col_map['compliance'],
            lambda x: x < 0.7
        )

        +

        safe_calc(
            active_df,
            col_map['budget'],
            lambda x: x > 0.12
        )

        +

        safe_calc(
            active_df,
            col_map['incentive'],
            lambda x: x == 0
        )

        +

        safe_calc(
            active_df,
            col_map['stock'],
            lambda x: x > 60
        )

        +

        safe_calc(
            active_df,
            col_map['wap'],
            lambda x: x <= 0.5
        )

        +

        safe_calc(
            active_df,
            col_map['visit'],
            lambda x: x <= 5
        )
    )

    # ==============================
    # RISK LOGIC
    # ==============================

    def risk(score):

        if score >= 6:
            return "High Risk"

        elif score == 5:
            return "Medium Risk"

        else:
            return "Low Risk"

    active_df['Risk_Level'] = (
        active_df['EWS_Score']
        .apply(risk)
    )

    print("\n📌 RISK LEVEL COUNTS:")
    print(
        active_df['Risk_Level']
        .value_counts()
    )

# ==============================
# MONTH
# ==============================

active_df['Month'] = month_name

# ==============================
# HISTORY FILE
# ==============================

hist_file = os.path.join(
    OUTPUT_FOLDER,
    "final_ews_data.csv"
)

if os.path.exists(hist_file):

    old = pd.read_csv(hist_file)

    combined = pd.concat(
        [old, active_df],
        ignore_index=True
    )

else:

    combined = active_df.copy()

combined.drop_duplicates(
    ['Employee ID', 'Month'],
    inplace=True
)

# ==============================
# PREVIOUS RISK
# ==============================

combined['Month_dt'] = pd.to_datetime(
    combined['Month'],
    format="%b-%y",
    errors='coerce'
)

combined = combined.sort_values(
    ['Employee ID', 'Month_dt']
)

combined['Prev_Risk'] = (
    combined.groupby('Employee ID')
    ['Risk_Level']
    .shift(1)
)

combined.drop(
    columns=['Month_dt'],
    inplace=True
)

combined.to_csv(
    hist_file,
    index=False
)

# ==============================
# CURRENT MONTH
# ==============================

current = combined[
    combined['Month'] == month_name
].copy()

# ==============================
# METRICS
# ==============================

total_high = (
    current['Risk_Level']
    == "High Risk"
).sum()

stayed = (

    (current['Prev_Risk']
     == "High Risk")

    &

    (current['Risk_Level']
     == "High Risk")

).sum()

improved = (

    (current['Prev_Risk']
     == "High Risk")

    &

    (current['Risk_Level']
     != "High Risk")

).sum()

new = (

    (
        (current['Prev_Risk']
         != "High Risk")

        |

        (current['Prev_Risk'].isna())
    )

    &

    (current['Risk_Level']
     == "High Risk")

).sum()

# ==============================
# AI PROMPT
# ==============================

prompt = f"""
You are an HR Risk Analyst.

IMPORTANT:
Still High Risk means no improvement.

Total High Risk: {total_high}
Still High Risk: {stayed}
Improved: {improved}
New High Risk: {new}

Give 4 short business insights.
"""

# ==============================
# AI API
# ==============================

client = SambaNova(

    api_key="458ece5c-f523-4e71-9f15-874013170cab",

    base_url="https://api.sambanova.ai/v1",
)

ai_text = None

for i in range(2):

    try:

        print(f"\n🤖 AI Attempt {i+1}")

        res = client.chat.completions.create(

            model="Meta-Llama-3.3-70B-Instruct",

            messages=[
                {
                    "role":"user",
                    "content":prompt
                }
            ],

            temperature=0.3,

            max_tokens=150
        )

        ai_text = (
            res.choices[0]
            .message.content
        )

        break

    except Exception as e:

        print("❌ AI Error:", e)

        time.sleep(2)

if ai_text is None:

    ai_text = f"""
- {total_high} employees are high risk
- {stayed} still high risk
- {improved} improved
- {new} new risk cases
"""

# ==============================
# SAVE REPORTS
# ==============================

csv_file = os.path.join(
    OUTPUT_FOLDER,
    f"ews_{month_name}.csv"
)

txt_file = os.path.join(
    OUTPUT_FOLDER,
    f"EWS_Report_{month_name}.txt"
)

current.to_csv(
    csv_file,
    index=False
)

with open(
    txt_file,
    "w",
    encoding="utf-8"
) as f:

    f.write(ai_text)

print("\n✅ REPORT GENERATED")
# ==============================
# AUTO GIT PUSH
# ==============================

try:

    print("\n📤 Uploading to GitHub...")

    subprocess.run(
        ["git", "pull", "origin", "main"],
        cwd=BASE_DIR,
        check=True
    )

    subprocess.run(
        ["git", "add", "."],
        cwd=BASE_DIR,
        check=True
    )

    subprocess.run(
        [
            "git",
            "commit",
            "-m",
            f"Auto update {month_name}"
        ],
        cwd=BASE_DIR,
        check=True
    )

    subprocess.run(
        ["git", "push", "origin", "main"],
        cwd=BASE_DIR,
        check=True
    )

    print("\n✅ GitHub Updated Successfully")

except Exception as e:

    print("\n❌ Git Push Failed")
    print(e)

print("\n🚀 AUTOMATION COMPLETED")