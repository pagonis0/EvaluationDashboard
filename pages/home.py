import dash
from dash import html, dcc

dash.register_page(__name__, path='/')

layout = html.Div([
    html.H1('This is our Home page'),
    html.Div([
        "Herzlich willkommen auf unserem leistungsstarken Bildungsanalyse-Dashboard! "
        "Hier bieten wir Ihnen einen umfassenden Überblick über die Leistung der Studierenden und die Analyse der Werkzeugnutzung, "
        "um Ihnen einen tiefen Einblick in die Feinheiten Ihrer Kurse zu ermöglichen. Unsere sorgfältig gestaltete Benutzeroberfläche bietet "
        "eine Vielzahl von erweiterten Filtern, die ein maßgeschneidertes Erlebnis für Ihre spezifischen Anforderungen gewährleisten."
        "Entdecken Sie die Geschichten hinter den Noten, während Sie durch den Abschnitt zur Leistung der Studierenden navigieren. "
        "Erhalten Sie Einblicke in Stärken, Schwächen und Trends, um datengesteuerte Entscheidungen für akademische Exzellenz zu treffen. "
        "Die interaktive Natur unseres Dashboards ermöglicht es Ihnen, Daten mühelos zu analysieren und ein tieferes Verständnis für den Lernprozess zu fördern."
        "Auf der anderen Seite erkunden Sie die Analyse der Werkzeugnutzung pro Kurs, um die Effektivität unserer Bildungswerkzeuge zu bewerten. "
        "Identifizieren Sie Muster, Nutzungsspitzen und Verbesserungsmöglichkeiten, alles präsentiert mit Klarheit durch intuitive Visualisierungen."
        " Dieser ganzheitliche Ansatz ermöglicht es Ihnen, Ihre Strategien zu optimieren und eine optimale Lernumgebung für Studierende und "
        "Lehrende zu gewährleisten."
        'This is our Home page content. Click ',
        dcc.Link('here', href='/usage', className='button-link'),
        ' for Usage, and click ',
        dcc.Link('here', href='/score', className='button-link'),
        ' for scores.'
    ]),
])
