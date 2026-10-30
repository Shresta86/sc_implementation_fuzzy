# Fuzzy Logic AC Controller - Software Prototype

Interactive simulator based on Pagare et al., "Reducing energy consumption in air conditioning
systems, a fuzzy logic-based optimization approach", Energy Reports 14 (2025) 3014-3032.

## Run it
    pip install -r requirements.txt
    streamlit run app.py
(opens in your browser at http://localhost:8501)

## Files
- fuzzy_core.py - the controller: membership functions, all 50 rules, Mamdani inference, centroid defuzzification, paper's energy formula
- app.py        - Streamlit entry point
- app_full.py   - full interface (4 tabs), including validation and boundary checks
- Test the core alone: `python fuzzy_core.py` (prints the paper-example check)

## Tabs
1. Live controller - move sliders (temp difference, humidity, voltage); see compressor, fan, mode, direction, membership graphs, and which rules fired
2. Room simulation - on/off thermostat vs fuzzy controller; try the input-scaling slider (our contribution)
3. Rule base - the paper's 50 rules
4. Paper check - reproduces the paper's worked example (7.16 C, 97 %, 220 V -> ~67 %, 938 rpm, 0.352, 31.7 deg)

## Limitations
The room model is a simple first-order toy model; the energy index is the paper's own hand-written formula.
It is a comparison tool, not a validated building simulation.
