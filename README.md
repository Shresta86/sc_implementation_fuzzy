
# sc_implementation_fuzzy
# Fuzzy Logic AC Controller

A Streamlit prototype of a fuzzy logic controller for an air conditioner. It re-implements the controller described in Pagare et al. (2025) and provides an interactive way to explore its rules, outputs, and a simplified room simulation.

> **Note:** This is a software prototype. The room simulation and energy index are simplified estimates, not results from a real AC unit or a validated building model.

## Project overview

The controller takes three inputs:

- Temperature difference between the room and the set point
- Relative humidity
- Supply voltage

It applies a 50-rule Mamdani fuzzy inference system and produces four outputs:

- Compressor speed
- Fan speed
- Operating mode: AC or dehumidifier
- Fan direction

## Features implemented

- Interactive controller controls and output display
- Input membership-function plots
- Display of rules that fire and their strengths
- Table of all 50 fuzzy rules
- Paper worked-example comparison
- Boundary-case checks for low and high input values
- Simplified comparison of an on/off thermostat and fuzzy control
- Experimental input scaling in the room simulation

The room simulation is included to explore controller behavior. Its results should not be interpreted as proof of real-world energy savings.

## Project structure

sc/
├── app.py          # Streamlit entry point
├── app_full.py     # Full four-tab Streamlit application
├── fuzzy_core.py   # Membership functions, rule base, inference, and energy index
├── requirements.txt
└── README.md

## Run locally

Python 3.10 or later is recommended.
git clone <your-repository-url>
cd sc
pip install -r requirements.txt
streamlit run app.py


Streamlit will print a local URL in the terminal, usually http://localhost:8501.

## Paper reference

Pagare, H., Mishra, K., Sharma, K., Kotecha, K., & Kulkarni, A. (2025). “Reducing energy consumption in air conditioning systems: A fuzzy logic-based optimization approach.” *Energy Reports, 14*, 3014–3032. https://doi.org/10.1016/j.egyr.2025.09.021

## Future work

- Test the controller with a more realistic building or room model
- Compare it with a PID controller under the same simulation conditions
- Add outdoor temperature and room occupancy as inputs
- Use realistic operating ranges and validate membership functions
- Test the controller with real AC hardware or measured data
- Improve energy and comfort evaluation using validated metrics
>>>>>>> 7896dd2862f96bef71fa3893371ddf612b3bd937
