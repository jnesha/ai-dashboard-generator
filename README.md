AI-Powered Dashboard Generator

Upload any CSV and this app figures out what's worth looking at. It profiles the data, sends a summary to Claude, and Claude decides which KPIs and charts make sense for that specific dataset. You can also tell it what to focus on, filter the results, ask follow-up questions about the data, and download a PDF report with the charts included.

Why I built this

Most dashboard tools make you manually pick every chart and metric yourself. I wanted to see if an AI model could look at a dataset the way an analyst would and make those calls on its own, then still let the user steer it with a simple focus field instead of a full analytics setup.

How it works

The app reads the CSV with pandas and builds a short profile of it, things like column types, missing values, min/max/average for numbers, and the top categories for text columns. That profile, not the raw data, gets sent to Claude. Claude responds with a short written summary, a handful of KPIs worth highlighting, and a few charts worth showing. The app then renders those with Plotly.

If you type something in the focus box, like "revenue by region," that gets added to the prompt so Claude leans toward metrics and charts related to what you actually care about instead of guessing.

There's also a filter section for any column with a small number of categories, and a question box at the bottom where you can ask things like "which region has the highest average order value" and get an answer based on the current filtered data.

Project files

app.py runs the Streamlit interface and handles rendering.
data_profiler.py turns a dataframe into the compact summary sent to Claude.
ai_analyzer.py calls the Claude API and parses the response.
report_builder.py builds the downloadable PDF, including the chart images.

Running it locally

Create a virtual environment and install the requirements:

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

You'll need an Anthropic API key from console.anthropic.com. Set it as an environment variable:

export ANTHROPIC_API_KEY="your-key-here"

Then run:

streamlit run app.py

To get PDF exports with actual chart images working, you also need to run this once:

plotly_get_chrome

That installs a small headless Chrome that Plotly uses in the background to turn charts into images. It's not something you open yourself, it just needs to be there.

What I'd add next

Right now every upload calls the API fresh, so there's no caching. I'd also want to validate Claude's chart recommendations more carefully before rendering them, right now it mostly trusts the response. And it hasn't been tested yet on anything much bigger than a few thousand rows.