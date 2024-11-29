import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np
from packages.retrieve_stats import get_leak_types, get_count_and_probabilities
from packages.plots import plot_regression
from packages.servicesanalisis import get_services_info

LEAKS_FILE = 'leak_types.txt'
CSV_FILE_RISK = 'services\services_risk_dimensions_cluster.csv'
CSV_SERVICE_DATA ='.\services\services.xlsx'
FIGURES_FOLDER = 'figures\leakregression'
VERBOSE = 1

def xy_regression(data, label, xlabel='x', ylabel='y'):
    """Fuction to create a regression from a dict and print results"""

    # Split data into X and Y
    X = np.array([val[0] for val in data.values()]).reshape(-1, 1)  # Mean
    Y = np.array([val[1] for val in data.values()])  # Score

    # Fit a linear regression model
    model = LinearRegression()
    model.fit(X, Y)

    # Regression line parameters
    slope = model.coef_[0]
    intercept = model.intercept_
    r_squared = model.score(X, Y)

    # Print results
    print(f"Regresion: {label}")
    print(f"Slope: {slope}")
    print(f"Intercept: {intercept}")
    print(f"R^2: {r_squared}\n")

    return plot_regression(X,Y,model,slope,intercept, label, xlabel, ylabel)


def leakregression(leaks_file=LEAKS_FILE):
    """Function to get the data from the leaks and create a regression between password strength in the leaks and their risk value"""
    # Get leaks
    leak_types = get_leak_types(leaks_file)
    leak_names = [x for x,y in leak_types]
    leak_names.sort()

    # Get the services data stored
    services = get_services_info(CSV_SERVICE_DATA)
    services['Website'] = services['Website'].str.lower()

    # Get the services corresponding to leaks
    leaked_services = services.loc[services['Website'].isin([x for x in leak_names])]
    leaked_services.reset_index(inplace=True)
    leaked_services_only_data = leaked_services.iloc[: ,12:30]

    # Get number of data colected by each leak
    leaked_services_only_data['sum'] = leaked_services_only_data.sum(axis=1, numeric_only=True)
    leaked_services_only_data['Website'] = leaked_services.loc[:, 'Website']
    services_count = leaked_services_only_data.loc[:, ['Website', 'sum']]

    # Get the services corresponding to the leaks
    services_count.reset_index(inplace=True)
    services_count = services_count.drop('index', axis=1)

    if VERBOSE > 0: print("Leaks count:\n", services_count)

    # Get risk for leaks, drop cluster column
    services_risks = pd.read_csv(CSV_FILE_RISK)
    services_risks = services_risks.drop(['Only data cluster', 'NIST Compliance Score'], axis=1)

    # Get the services corresponding to the leaks
    services_risks['Website'] = services_risks['Website'].str.lower().str.strip()
    services_risks = services_risks.loc[services_risks['Website'].isin([x for x in leak_names])]
    services_risks.reset_index(inplace=True)
    services_risks = services_risks.drop('index', axis=1)

    if VERBOSE > 0: print("\nLeaks risk:\n", services_risks)

    # Calculate mean score for each leak and store it in dict with risk and count
    leaks_score_risk = {}
    leaks_score_count = {}
    for leak in leak_names:
        # Calculate leak mean by multiplying probabilities
        scores = [0,1,2,3,4]
        leak_count_prob = get_count_and_probabilities(leak)
        mean = sum([a*b for a,b in zip(leak_count_prob[1],scores)])

        # Get risk
        risk = services_risks.loc[services_risks['Website'] == leak, 'Risk sum'].values

        # Get number of data collected
        count = services_count.loc[services_count['Website'] == leak, 'sum'].values
        
        # If risk found append to dict
        if risk:
            risk = int(risk[0])
            # Append mean and risk to dict
            leaks_score_risk[leak] = mean, risk
            leaks_score_count[leak] = mean, count
        else:
            print(leak)

    # Add the strength to the data frame
    leaked_services_only_data['strength'] = leaked_services_only_data['Website'].map(leaks_score_risk)


    # Regression with scores
    risk_regression = xy_regression(leaks_score_risk, 'Risk vs stregnth', xlabel='Password strength', ylabel='Service risk')
    risk_regression.savefig(f"{FIGURES_FOLDER}\\risk_regresion.png")
    risk_regression.close() 

    # Regression with count
    count_regression = xy_regression(leaks_score_count, 'Data collected count vs strenght', xlabel='Password strength', ylabel='Service data collected count')
    count_regression.savefig(f"{FIGURES_FOLDER}\\count_regresion.png")
    count_regression.close()

    # Multivariate regression type of data collected vs strength
    print(leaked_services_only_data[['Website', 'strength']])
    
    return