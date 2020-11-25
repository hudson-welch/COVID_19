# COVID_19

This API gets the latest data reported for COVID19 cases and deaths and produces graphs that compare selected states and counties to the US.
Lower case variables are daily numbers: cases, deaths, cpm, dpm  
Upper case variables are cumulative: CASES, DEATHS, CPM, DPM
CPM and cpm are cases per million inhabitants
DPM and dpm are deaths per million inhabitants

To use this you need to set up authentication for [kaggle's API](https://www.kaggle.com/docs/api)
This involves getting authorization codes from kaggle and storing this in a specific directory

You will need to download the count_pop.csv and state_populations.xlsx files into the same directory you run the notebook. 
