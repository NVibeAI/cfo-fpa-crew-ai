# 🚀 Quick Start Guide - FP&A CFO Crew AI

## ✅ Project Status: **COMPLETE & READY TO RUN**

---

## 📋 Step-by-Step Setup

### 1. Install Dependencies

Open PowerShell/Terminal in the project folder and run:

```powershell
pip install -r requirements.txt
```

**Expected output:** All packages install successfully

---

### 2. Set OpenAI API Key

**Option A: PowerShell (temporary for current session)**
```powershell
$env:OPENAI_API_KEY="sk-your-key-here"
```

**Option B: Create .env file (permanent)**
Create a file named `.env` in the project root:
```
OPENAI_API_KEY=sk-your-key-here
```

**Option C: System Environment Variable**
- Windows: Settings → System → Environment Variables → Add `OPENAI_API_KEY`

---

## 🎯 How to Run

### **Method 1: Run Individual Task Scripts**

Run each task in order:

```powershell
# Step 1: Data Integration (creates unified_financials.csv)
python tasks/data_integration.py

# Step 2: FP&A Forecast
python tasks/fpna_forecast.py

# Step 3: Profit Simulation
python tasks/profit_simulation.py

# Step 4: Executive Summary
python tasks/executive_summary.py
```

**Output Location:** 
- Console/terminal where you run the script
- `data/unified_financials.csv` (created by data_integration.py)

---

### **Method 2: Streamlit Dashboard (Interactive UI)**

Launch the web dashboard:

```powershell
streamlit run dashboards/fpna_dashboard.py
```

**What happens:**
1. Dashboard opens in your browser (usually `http://localhost:8501`)
2. Click buttons in the sidebar to run agents:
   - 🧩 Data Connector
   - 📊 FP&A Forecast  
   - 💰 Profit Simulation
   - 🧑‍💼 CFO Summary

**Output Location:**
- Browser window (text areas show results)
- Charts and data tables displayed in the main panel

---

## 📊 Where to See Output

### **Console/Terminal Output:**
- When running `.py` scripts directly, output appears in your terminal
- Look for sections marked with `=====` separators
- Final results are printed after `RESULT:` section

### **Dashboard Output:**
- Main panel shows data tables and charts
- Sidebar text areas show agent responses
- Success messages appear when tasks complete

### **File Output:**
- `data/unified_financials.csv` - Generated unified dataset
- Created automatically when you run Data Connector

---

## 🔍 Verify It's Working

1. **Check API Key:**
   ```powershell
   echo $env:OPENAI_API_KEY
   ```
   Should show your key (not empty)

2. **Test Data Integration:**
   ```powershell
   python tasks/data_integration.py
   ```
   Should create `data/unified_financials.csv` and print results

3. **Check Dashboard:**
   ```powershell
   streamlit run dashboards/fpna_dashboard.py
   ```
   Browser should open with the dashboard interface

---

## ⚠️ Troubleshooting

### Error: "OPENAI_API_KEY not found"
- Make sure you set the environment variable
- Restart your terminal/IDE after setting it
- Check `.env` file format (no quotes, no spaces around `=`)

### Error: "Module not found"
- Run: `pip install -r requirements.txt`
- Make sure you're in the project directory

### Error: "unified_financials.csv not found"
- Run `python tasks/data_integration.py` first
- Check that `data/` folder exists with sample CSV files

### Dashboard not opening
- Check if port 8501 is already in use
- Try: `streamlit run dashboards/fpna_dashboard.py --server.port 8502`

---

## 📁 Project Structure

```
fpna_cfo_crew_ai/
├── crew_config.py          # Agent & Crew configuration
├── llm_openai.py           # OpenAI LLM setup
├── tasks/                   # Individual task scripts
│   ├── data_integration.py
│   ├── fpna_forecast.py
│   ├── profit_simulation.py
│   └── executive_summary.py
├── data/                    # Input data & generated output
│   ├── sap_costs.csv
│   ├── salesforce_deals.csv
│   ├── financial_summary.csv
│   └── unified_financials.csv (generated)
├── dashboards/              # Streamlit dashboard
│   └── fpna_dashboard.py
├── requirements.txt         # Dependencies
└── README.md               # Full documentation
```

---

## 🎉 Success Indicators

✅ **Setup Complete When:**
- All packages installed without errors
- API key is set and accessible
- Sample data files exist in `data/` folder

✅ **Running Successfully When:**
- Tasks execute without errors
- AI agents generate responses
- Dashboard loads and buttons work
- `unified_financials.csv` is created

---

## 🆘 Need Help?

1. Check the full `README.md` for detailed documentation
2. Verify all files are in the correct folders
3. Ensure Python 3.10+ is installed
4. Check OpenAI API key is valid and has credits

---

**Ready to go!** Start with `python tasks/data_integration.py` or launch the dashboard! 🚀


