import pandas as pd

df = pd.read_excel("validate.xlsx")
print(df.head())

from analysisrag import get_vulnerabilities

for i in range(len(df)):
    code = df.iloc[i]["code"]
    vulnerabilities = get_vulnerabilities(code)
    df.at[i, "vulnerabilities"] = str(vulnerabilities)