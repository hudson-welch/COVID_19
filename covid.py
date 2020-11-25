# William Hudson Welch
# 19 November 2020
# This API gets the latest data reported for COVID19 cases and deaths
# and produces graphs that compare selected states and counties to the US.
# Lower case variables are daily numbers: cases, deaths, cpm, dpm  
# Upper case variables are cumulative: CASES, DEATHS, CPM, DPM
# CPM and cpm are cases per million inhabitants
# DPM and dpm are deaths per million inhabitants


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import kaggle as kg
import pygal

#### Get and prepare data ###############################################

def get_kaggle():
	kg.api.authenticate()
	kg.api.dataset_download_files(dataset="paultimothymooney/nytimes-covid19-data",
							      path='covid-19-data-master.zip', unzip=True)

def get_governor():
	gov = pd.read_csv("governors - Sheet1.csv")
	import re
	states = []
	for i, r in gov.iterrows():
		state = r.state_of
		# result = re.search('(of )(\w+\s*\w*)', state)
		result = re.search('(of )(.*)', state)
		states.append(result.group(2))
	gov['state'] = states
	gov['color'] = np.where(gov.party=="Republican", "red", "blue")
	gov = gov[["state", "party", "color"]]
	return gov


def get_us():
	us = pd.read_csv("covid-19-data-master.zip/us.csv", encoding='ISO-8859-1')
	us['date'] = pd.to_datetime(us.date, format="%Y-%m-%d")
	us_pop = 329227746
	us["CPM"] = 1e6 * us.cases / us_pop
	us["DPM"] = 1e6 * us.deaths / us_pop
	us.rename(columns={'cases': 'CASES', 'deaths': 'DEATHS'}, inplace=True)
	us['cases'] = us.CASES.diff()
	us['deaths'] = us.DEATHS.diff()
	us['cpm'] = us.CPM.diff()
	us['dpm'] = us.DPM.diff()
	us.dropna(inplace=True)
	return us

def get_state():
	st = pd.read_csv("covid-19-data-master.zip/us-states.csv", 
					encoding='ISO-8859-1')
	st['date'] = pd.to_datetime(st.date, format="%Y-%m-%d")
	stpop = pd.read_excel("state_populations.xlsx")
	st = pd.merge(st, stpop, left_on='state', right_on='state')
	st.rename(columns={'cases': 'CASES', 'deaths': 'DEATHS'}, inplace=True)
	st["CPM"] = 1e6 * st.CASES / st.population
	st["DPM"] = 1e6 * st.DEATHS / st.population
	st['cases'] = st.CASES.diff()
	st['deaths'] = st.DEATHS.diff()
	st['cpm'] = st.CPM.diff()
	st['dpm'] = st.DPM.diff()
	st = st[["date",  "state", "CASES", "DEATHS", "CPM", "DPM", 
			 "cases", "deaths", "cpm", "dpm", "population"]]
	st.loc[st.cases<0, ['cases', 'deaths', 'cpm', 'dpm']] = [np.NaN, np.NaN, np.NaN, np.NaN]
	# print(earliest)
	return st

def get_county():
	ct = pd.read_csv('covid-19-data-master.zip/us-counties.csv', 
					encoding='ISO-8859-1')
	ct['date'] = pd.to_datetime(ct.date, format="%Y-%m-%d")
	ctpop = pd.read_csv("county_pop.csv")
	latest_year = ctpop.Year.max()
	ctpop_lastest = ctpop[ctpop.Year == latest_year]
	ct = pd.merge(ct, ctpop_lastest, left_on='fips', right_on='FIPS')
	ct = ct.rename(columns={"Population": "population"})
	ct.rename(columns={'cases': 'CASES', 'deaths': 'DEATHS'}, inplace=True)
	ct["CPM"] = 1e6 * ct.CASES / ct.population
	ct["DPM"] = 1e6 * ct.DEATHS / ct.population
	ct['cases'] = ct.CASES.diff()
	ct['deaths'] = ct.DEATHS.diff()
	ct['cpm'] = ct.CPM.diff()
	ct['dpm'] = ct.DPM.diff()
	ct = ct[["date", "county", "state", "CASES", "DEATHS", "CPM", "DPM", 
			 "cases", "deaths", "cpm", "dpm", "FIPS", "population"]]
	ct.loc[ct.cases<0, ['cases', 'deaths', 'cpm', 'dpm']] = [np.NaN, np.NaN, np.NaN, np.NaN]
	return ct

def setup(update=True):
    if update:
        get_kaggle()

    us = get_us()
    st = get_state()
    ct = get_county()
    #gov = get_governor()
    return us, st, ct
def prep_data(df, param="cpm"):
    """prep simple dataframe for pygal"""
    df = df.copy()
    df['roll'] = round(df[param].rolling(window=7).mean())
    df.dropna(inplace=True)
    pdat = [(dt, val) for dt, val in zip(df.date, df.roll)]
    return pdat

def prep_data2(df, col='Florida'):
    """prep pivoted dataframe for pygal"""
    df = df.copy()
    df['roll'] = round(df[col].rolling(window=7).mean())
    df.dropna(inplace=True)
    pdat = [(dt, val) for dt, val in zip(df.date, df.roll)]
    return pdat
    

def prep_states(df, states=['Florida', 'North Carolina', 'Texas'], param='cpm'):
    #df = df.set_index('date')
    mask = df['state'].isin(states)
    df = df[mask].copy()
    # The method below includes the name of the parameter 
    #df = df[['date', 'state', param]]
    #df = df.pivot(index='date', columns='state').copy()
    # As opposed to this method which does not
    df = df.pivot(index='date', columns='state', values=param).copy()
    df.dropna(inplace=True)
    df.reset_index(inplace=True)
    return df

def prep_counties(df, counties, param='cpm'):
    mask = df['FIPS'].isin(counties.FIPS)
    df = df[mask].copy()
    df = df.pivot(index='date', columns='FIPS', values=param).copy()
    df.dropna(inplace=True)
    df.reset_index(inplace=True)
    return df


def get_FIPS(df, counties):
    fips = []
    for i, r in counties.iterrows():
        mask1 = r.county==df.county
        mask2 = r.state==df.state
        mask3 = mask1 & mask2
        fip = df[mask3].FIPS.unique()[0]
        fips.append(fip)
        #print(i, r.state, r.county, fip)
    
    counties['FIPS'] = fips
    return counties


###### plots ######################################################

def deaths(df):
    fig, ax = plt.subplots(figsize=(12,6))
    ax.plot(df.date, df.deaths, label='deaths')
    ax.set_title("COVID19 deaths")
    plt.xticks(rotation=90)
    ax.set_ylabel("deaths")
    ax.legend()
    plt.show()

def cases(df):
    fig, ax = plt.subplots(figsize=(12,6))
    ax.plot(df.date, df.cases, label='cases')
    ax.set_title("COVID19 cases")
    plt.xticks(rotation=90)
    ax.set_ylabel("cases")
    ax.legend()
    plt.show()

def rolling(us, df):
	g = sns.factorplot(x="date", y="CPM", hue='state', data=df)
	plt.show()

import re

def plot_group(us=None, st=None, ct=None, 
               states=None, counties=None, param='cpm',
               fname='COVID19.svg'):
    if param == 'cpm':
        tit = "Cases per million residents"
        laby = "CPM"
    elif param == 'dpm':
        tit = "Deaths per million residents"
        laby = "DPM"
    elif re.match('.*[A-Z].*', param):
        tit = 'Cummulative ' + param.lower()
        laby = param
    else:
        tit = param.capitalize()
        laby = param
   
        
    datetimeline = pygal.DateTimeLine(title=tit, y_title=laby,
        x_label_rotation=35, truncate_label=-1,
        x_value_formatter=lambda dt: dt.strftime('%d %b %Y')
        )
    if us is not None:
        datetimeline.add('US', prep_data(us, param))
    if st is not None:
        pst = prep_states(st, states, param)
        for state in states:
            datetimeline.add(state, prep_data2(pst, state))
    if ct is not None:
        pct = prep_counties(ct, counties, param)
        for i, r in counties.iterrows():
            datetimeline.add(r.county, prep_data2(pct, r.FIPS))

    datetimeline.render_to_file(fname)
    datetimeline.render_in_browser(height = 300)
    

