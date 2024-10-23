# DiscSim

This code was written for [`CEGIS`](https://www.cegis.org/) (Center for Effective Governance of Indian States), an organization that aims to help state governments in India achieve better development outcomes.

An important goal of CEGIS is to improve the quality of administrative data collected by state governments. One way in which this is achieved is to re-sample a subset of the data and measure the deviation from the original samples collected. These deviations are quantified as 'discrepancy scores', and large discrepancy scores are flagged for intervention by a third party.

Often, it is not clear what re-sampling strategy should be used to obtain the most accurate and reliable discrepancy scores. The goal of this project is to create a simulator to predict discrepancy scores, and the statistical accuracy of the discrepancy scores, for different re-sampling strategies. This repository will be populated with python scripts and jupyter notebooks to implement the simulator. However, no data will be made public as it is sensitive data collected by state governments in India.

DiscSim is a simulation tool with a backend API built using FastAPI and a frontend interface developed with Streamlit. The project is containerized using Docker for easy deployment.

## Getting Started

### Cloning the Repository

```bash
git clone https://github.com/cegis-org/discsim.git
cd DiscSim
```

### Setting Up a Virtual Environment

You can set up the virtual environment using either `conda` or `venv`. Below are the instructions for both.

#### Using Conda

1. Create the environment:

   ```bash
   conda create -n venv python=3.11
   ```

2. Activate the environment:

   ```bash
   conda activate venv
   ```

#### Using venv

1. Create the environment:

   ```bash
   python -m venv venv
   ```

2. Activate the environment:

   - On Windows:

     ```bash
     venv\Scripts\activate
     ```

   - On macOS/Linux:

     ```bash
     source venv/bin/activate
     ```

### Installing Dependencies

With the virtual environment activated, run:

```bash
pip install -r requirements.txt
```

## Running the Application

You can run the API server and the Streamlit frontend in a few different ways.

### Running the API backend, SQL Server, and the Streamlit frontend

**Using Docker:**

   ```bash
   docker-compose build
   docker-compose up
   ```

1. Your API server is now running on http://localhost:8000,
2. The PostgreSQL will be running on http://localhost:5432
3. And the frontend on http://localhost:8501 - this is the link you'll be opening on your browser to see it in action!

## Contributing

Feel free to fork this repository and submit pull requests. For major changes, please open an issue first to discuss what you would like to change.

---

Thank you for checking out DiscSim! 🚀
