import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from openpyxl import load_workbook

# Load the dataset (replace the file path with your own)
file_path = "Auflistung Gruppen.xlsx"
mydata = pd.read_excel(file_path)

# Fixing data types
mydata['note_org'] = pd.to_numeric(mydata['note_org'], errors='coerce')
mydata['titel'] = mydata['titel'].astype('category')
mydata['stg'] = mydata['stg'].astype('category')
mydata['prf'] = mydata['prf'].astype('category')
mydata['kurs'] = mydata['kurs'].astype('category')
mydata['anmeldung_2'] = mydata['anmeldung_2'].astype('category')
mydata['anmeldung_3'] = mydata['anmeldung_3'].astype('category')

mydata_na = mydata.dropna(subset=['note_org'])
# Handling missing data
mydata['note_org'] = mydata['note_org'].fillna(5)


# Creating categorical variables
mydata['note_cat'] = mydata['note_org'].apply(lambda x: 'Bestanden' if x <= 4 else 'Nicht bestanden')
mydata_na['note_cat'] = mydata_na['note_org'].apply(lambda x: 'Bestanden' if x <= 4 else 'Nicht bestanden')

# Counts and percentages for the first plot
freq_mydata_na = len(mydata_na)
freq_mydata = len(mydata)
freq_not_na = freq_mydata - freq_mydata_na

percent_mydata_na = round((freq_mydata_na / freq_mydata) * 100, 2)
percent_not_na = round((freq_not_na / freq_mydata) * 100, 2)

# Create plot data
plot_data = pd.DataFrame({
    'group': ['An den Prüfungen teilgenommen', 'Nicht an den Prüfungen teilgenommen'],
    'frequency': [freq_mydata_na, freq_not_na],
    'percentage': [percent_mydata_na, percent_not_na]
})

# Plot 1 - Bar Plot
fig1 = go.Figure(go.Bar(
    x=plot_data['group'],
    y=plot_data['frequency'],
    text=plot_data['percentage'].apply(lambda x: f"{x}% ({int(x * freq_mydata / 100)} Studierenden)"),
    textposition='outside',
    marker_color=['#cc79a7', '#d55e00']
))

fig1.update_layout(
    title="Anzahl der Studierenden, die nach der Anmeldung an Prüfungen teilgenommen haben",
    xaxis_title=None,
    yaxis_title="Absolutzahlen",
    barmode='group'
)

# Save as JSON
fig1.write_json("plot1.json")

# Plot 2 - Bar plot for successAI and THI Moodle
mydata_na_true = mydata_na[mydata_na['kurs'] == True]
mydata_na_false = mydata_na[mydata_na['kurs'] == False]

# Calculate frequencies for plot 2
freq_mydata_na_true = len(mydata_na_true)
freq_mydata_na_false = len(mydata_na_false)


plot_data2 = pd.DataFrame({
    'group': ['SuccessAI Moodle', 'THI Moodle'],
    'frequency': [freq_mydata_na_true, freq_mydata_na_false],
    'kurs': ['SuccessAI Moodle', 'THI Moodle']
})

# Reorder the levels of the 'kurs' variable
# Ensure that sum of frequencies is not zero
total_frequency = sum(plot_data2['frequency'])
plot_data2['text'] = plot_data2['frequency'].apply(
    lambda x: f"{round(x / total_frequency * 100)}%" if total_frequency > 0 else "No data"
)

# Now use the updated 'text' in the plot
fig2 = go.Figure(go.Bar(
    x=plot_data2['kurs'],
    y=plot_data2['frequency'],
    text=plot_data2['text'],
    textposition='outside',
    marker_color=['#d55e00', '#cc79a7']
))

fig2.update_layout(
    title="Anwesenheit von Studierenden bei Prüfungen nach Moodle-Plattform",
    xaxis_title="Plattform",
    yaxis_title="Absolutzahlen"
)

# Save as JSON
fig2.write_json("plot2.json")

# Box plot for Noten pro Kurs
fill_colors = {"EI": "#d55e00", "WINF": "#cc79a7", "KI": "#0072b2"}
border_colors = {"EI": "black", "WINF": "black", "KI": "black"}

fig3 = px.box(mydata_na, x="titel", y="note_org", color="stg", 
              color_discrete_map=fill_colors,
              category_orders={'stg': ['EI', 'WINF', 'KI']})
fig3.update_layout(
    title="Noten pro Kurs",
    xaxis_title="Kurs",
    yaxis_title="Noten",
    boxmode="group"
)

fig3.write_json("plot3.json")

# Box plot for Noten pro Studiengang
fig4 = px.box(mydata_na, x="stg", y="note_org", color="stg",
              color_discrete_map=fill_colors, 
              category_orders={'stg': ['EI', 'IW', 'KI']})

fig4.update_layout(
    title="Noten pro Studiengang",
    xaxis_title="Studiengang",
    yaxis_title="Noten"
)

fig4.write_json("plot4.json")

# Boxplot per kurs (for the Analysis part)
fig5 = px.box(mydata_na, x="kurs", y="note_org", color="kurs",
              color_discrete_map={False: "#d55e00", True: "#cc79a7"})


fig5.update_layout(
    title="Vergleich der Noten",
    xaxis_title="Plattform",
    yaxis_title="Noten"
)

fig5.write_json("plot5.json")

# Density plot of Noten for kurs
fig6 = px.histogram(
    mydata_na, x="note_org", color="kurs", 
    marginal="rug",  # Adds a marginal rug plot on the axis
    opacity=0.5, 
    histnorm='density',  # Normalize to density to get a similar effect to density plot
    color_discrete_map={False: "#d55e00", True: "#cc79a7"},
    labels={"note_org": "Noten", "kurs": "Plattform"}
)

fig6.update_layout(
    title="Dichtediagramm der Noten",
    xaxis_title="Noten",
    yaxis_title="Density",
    barmode="overlay",  # Overlay the histograms for each kurs
    plot_bgcolor="white",  # Background color for the plot
)

fig6.write_json("plot6.json")

# Step 1: Calculate percentage frequencies
mydata_na['count'] = 1
data_percent = mydata_na.groupby(['note_org', 'kurs']).count().reset_index()
total_counts = data_percent.groupby('note_org')['count'].transform('sum')
data_percent['percentage'] = (data_percent['count'] / total_counts) * 100

# Step 2: Create the bar plot using Plotly Express
fig7 = px.bar(
    data_percent, 
    x="note_org", 
    y="percentage",  # Use the calculated percentage
    color="kurs", 
    barmode="group",  # Group bars side by side
    color_discrete_map={False: "#d55e00", True: "#cc79a7"},  # Custom colors
    labels={"note_org": "Noten", "percentage": "Percentage (%)", "kurs": "Platform"},  # Axis labels
    title="Bar Plot der Noten",  # Title of the plot
)

# Step 3: Update layout for styling and background
fig7.update_layout(
    xaxis_title="Noten",  # X-axis label
    yaxis_title="Percentage (%)",  # Y-axis label
    barmode="group",  # Ensure bars are side by side
    plot_bgcolor="white",  # White background for the plot
    title_x=0.5  # Center the title
)

# Optional: Save the plot to JSON if needed
fig7.write_json("plot7.json")

# Box plot for Verteilung der Noten nach Studiengang
fig8 = px.box(mydata_na, x="stg", y="note_org", color="kurs",
              color_discrete_map={False: "#d55e00", True: "#cc79a7"})
fig8.update_layout(
    title="Verteilung der Noten nach Studiengang",
    xaxis_title="Studiengang",
    yaxis_title="Noten"
)

fig8.write_json("plot8.json")

# Density Plot for stg
fig9 = px.histogram(
    mydata, x="note_org", color="kurs", 
    facet_col="stg", marginal="rug",
    opacity=0.5, 
    histnorm='density',
    color_discrete_map={False: "#d55e00", True: "#cc79a7"},
    labels={"note_org": "Noten", "kurs": "Plattform"})
fig9.update_layout(
    title="Verteilung der Noten nach Studiengang",
    xaxis_title="Noten",
    yaxis_title="Density",
    barmode="overlay",  # Overlay the histograms for each kurs
    plot_bgcolor="white",  # Background color for the plot
)

fig9.write_json("plot9.json")

# Box plot for Vergleich der Durchschnittsnoten
fig10 = px.box(mydata, x="titel", y="note_org", color="kurs", 
               color_discrete_map={False: "#d55e00", True: "#cc79a7"})
fig10.update_layout(
    title="Vergleich der Durchschnittsnoten",
    xaxis_title="Kurs",
    yaxis_title="Noten"
)

fig10.write_json("plot10.json")

# Contingency table plot for Bestanden oder nicht bestanden (All)
contingency_table = pd.crosstab(mydata['note_cat'], mydata['kurs']).reset_index()

# Melt the DataFrame to make it long-form
contingency_table_long = contingency_table.melt(id_vars='note_cat', value_vars=contingency_table.columns[1:], 
                                                var_name='kurs', value_name='count')

# Plot with color mapping based on `kurs`
fig11 = px.bar(
    contingency_table_long,
    x='note_cat',  # X-axis is 'note_cat' (Bestanden or Nicht Bestanden)
    y='count',     # Y-axis is the count of each group
    color='kurs',  # Use 'kurs' for color to apply color mapping
    color_discrete_map={False: "#d55e00", True: "#cc79a7"},  # Custom colors
    labels={"note_cat": "Noten", "count": "Percentage", "kurs": "Plattform"}  # Labels
)

# Update layout for titles
fig11.update_layout(
    title="Bestanden oder nicht bestanden (Alle)",
    xaxis_title="Noten",
    yaxis_title="Frequency",
    barmode="group"  # Side-by-side grouping
)

# Save the plot to a JSON file
fig11.write_json("plot11.json")


# Contingency table plot for Bestanden oder nicht bestanden (Erschien in Prüfungen)
contingency_table = pd.crosstab(mydata_na['note_cat'], mydata_na['kurs']).reset_index()

# Melt the DataFrame to make it long-form
contingency_table_long = contingency_table.melt(id_vars='note_cat', value_vars=contingency_table.columns[1:], 
                                                var_name='kurs', value_name='count')

# Plot with color mapping based on `kurs`
fig12 = px.bar(
    contingency_table_long,
    x='note_cat',  # X-axis is 'note_cat' (Bestanden or Nicht Bestanden)
    y='count',     # Y-axis is the count of each group
    color='kurs',  # Use 'kurs' for color to apply color mapping
    color_discrete_map={False: "#d55e00", True: "#cc79a7"},  # Custom colors
    labels={"note_cat": "Noten", "count": "Percentage", "kurs": "Plattform"}  # Labels
)

# Update layout for titles
fig12.update_layout(
    title="Bestanden oder nicht bestanden (Alle)",
    xaxis_title="Noten",
    yaxis_title="Frequency",
    barmode="group"  # Side-by-side grouping
)

# Save the plot to a JSON file
fig12.write_json("plot12.json")