import requests
import html
from urllib.parse import urlencode

# Place your ADS API token in a file with suitable permissions
with open('token', 'r') as file:
    token = file.read().rstrip()

# Identifier of the FLAMINGO ADS library
library = 'PU1J-aufRMujuhkIIRyxzA'

# Query list of papers
print('Querying ADS library for paper list')
results = requests.get(f"https://api.adsabs.harvard.edu/v1/biblib/libraries/{library}",
                       headers={'Authorization': 'Bearer ' + token})
bibcodes = results.json()['documents']

# Loop through and process each paper
papers = []
for i_bibcode, bibcode in enumerate(bibcodes):
    # Query paper data
    print(f'Querying paper: {i_bibcode+1}/{len(bibcodes)}')
    # TODO: Query multiple papers at the same time
    encoded_query = urlencode({"q": f"bibcode:{bibcode}", 'fl': 'title,author,pubdate,date,pub,identifier,year'})
    results = requests.get("https://api.adsabs.harvard.edu/v1/search/query?{}".format(encoded_query),
                           headers={'Authorization': 'Bearer ' + token})
    result = dict(results.json()['response']['docs'][0])

    # Generate author list
    if len(result['author']) < 20:
        author = ''
        for a in result['author']:
            last, first = a.split(', ')
            author += first + ' ' + last + ', '
        author = author[:-2] # Remove trailing ', '
    else:
        last, first = result['author'][0].split(', ')
        author = first + ' ' + last + ' et al.'

    # Determine arxiv identifier
    arxiv_identifier = ''
    for identifier in result['identifier']:
        if 'arXiv:' in identifier:
            arxiv_identifier = identifier.replace('arXiv:', '')
    if arxiv_identifier == '':
        print(f'Arxiv link not found for: {bibcode}')
        exit()

    # Shorter name for journal
    journal = {
            'arXiv e-prints': 'arxiv',
            'Monthly Notices of the Royal Astronomical Society': 'MNRAS',
    }.get(result['pub'], '')
    if journal == '':
        print('Journal not recognised:', result['pub'])
        journal = result['pub']

    # Save paper data
    data = (
        html.escape(result['title'][0]), # Escape troublesome characters
        author,
        f'https://ui.adsabs.harvard.edu/abs/{bibcode}',
        f'https://arxiv.org/abs/{arxiv_identifier}',
        journal,
        result['year'],
    )
    papers.append(data)

# Sort based on arxiv identifier
papers = sorted(papers, key=lambda d: d[3])

# Write basic html file, which will be formatter with make_webpage.py
with open('src/pages/papers.html', 'w') as file:
    file.write('<h1>FLAMINGO publications</h1>\n')
    file.write('This page contains a list of publications submitted to arXiv which make use of the FLAMINGO simulations. The papers are listed in chronological order based on when they were uploaded to arXiv. Please let us know if we have missed your paper!\n\n')

    file.write('<ol>\n')

    for paper in papers:
        file.write(f'<li><p><h5>{paper[0]}</h5>\n')
        file.write(f'<i>{paper[1]}</i><br>\n')
        file.write(f'{paper[4]} ({paper[5]}), ')
        file.write(f'<a href="{paper[2]}" class="active text-decoration-none">ADS</a>, ')
        file.write(f'<a href="{paper[3]}" class="active text-decoration-none">arXiv</a></p></li>\n')

    file.write('</ol>\n')

