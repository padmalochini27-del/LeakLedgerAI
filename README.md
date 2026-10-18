\# ⚡ LeakLedger AI



\*\*A local-first AI assistant for investigating household electricity consumption.\*\*



LeakLedger AI combines deterministic Python calculations with a locally running Gemma model to help users understand estimated household energy use and decide what to investigate next.



\## Features



\- Estimate daily and period electricity consumption in kWh.

\- Estimate electricity costs using a user-provided tariff.

\- Compare appliance-level energy estimates.

\- Visualize estimated consumption with a chart.

\- Ask a local AI model for an explanation and safe investigation suggestions.

\- Export appliance estimates to CSV.

\- Run inference locally using Ollama and Gemma 3 1B.



\## Technology Stack



\- Python

\- Streamlit

\- Pandas

\- Ollama

\- Gemma 3 1B



\## Getting Started



\### Prerequisites



Install Python and Ollama. Download the model:



```bash

ollama pull gemma3:1b

```



\### Installation



Clone this repository, then open a terminal inside the project directory.



```bash

python -m venv .venv

```



On Windows Command Prompt:



```cmd

.venv\\Scripts\\activate

python -m pip install -r requirements.txt

```



\### Run the application



```bash

streamlit run app.py

```



Open the local URL displayed in your terminal, usually `http://localhost:8501`.



\## How It Works



Python calculates estimated energy using:



`Energy (kWh) = Power (W) × Hours per day × Quantity × Days ÷ 1000`



Estimated cost is:



`Estimated cost = Estimated energy (kWh) × User-provided tariff`



Python generates the calculations and ranking. Gemma provides a natural-language explanation; its output may contain errors and should not be treated as the source of numerical truth.



\## Why Local AI?



Running Gemma through Ollama allows inference on the user's computer without requiring a cloud AI API. This can reduce the need to send household usage details to a third-party AI service and gives users more control over their model environment.



The app is designed for local inference. Users should still review the privacy and security of their own computer and installed software.



\## Limitations and Safety



\- Results are estimates based on user-entered values, not live meter readings.

\- Rated wattage multiplied by elapsed operating time may overestimate consumption for appliances that cycle on and off.

\- Actual electricity bills may include tariff slabs, fixed charges, taxes, and other fees.

\- AI-generated explanations may be inaccurate.

\- The app does not detect electrical faults, guarantee savings, or replace a qualified electrician.



\## Future Improvements



\- Compare estimates with manually entered meter readings.

\- Add bill-period comparisons.

\- Improve validation and automated calculation tests.

\- Support more appliance-specific operating assumptions.



\## License



This project is intended as an open-source learning project. A license can be added before public distribution.



