import requests
import html
from urllib.parse import urlencode

def query_ads_library(library):

    # Place your ADS API token in a file with suitable permissions
    with open('ADS_token', 'r') as file:
        token = file.read().rstrip()

    # Get list of papers in the library
    print('Querying ADS library for paper list')
    bibcodes = []
    headers = {'Authorization': 'Bearer ' + token}
    rows = 40

    # Initial query, get total number of papers
    query = f"https://api.adsabs.harvard.edu/v1/biblib/libraries/{library}?rows={rows}&start={len(bibcodes)}"
    results = requests.get(query, headers=headers)
    n_bibcodes_in_library = results.json()['metadata']['num_documents']
    bibcodes += results.json()['documents']

    # Pagination
    while len(bibcodes) < n_bibcodes_in_library:
        query = f"https://api.adsabs.harvard.edu/v1/biblib/libraries/{library}?rows={rows}&start={len(bibcodes)}"
        results = requests.get(query, headers=headers)
        bibcodes += results.json()['documents']

    # Use the API to get information for the papers
    papers = []
    rows = 10  # How many papers to include for each API call
    for i in range(0, len(bibcodes), rows):
        bibcode_query = f'bibcode:{bibcodes[i]}'
        for j in range(1, rows):
            if i + j < len(bibcodes):
                bibcode_query += f' OR bibcode:{bibcodes[i+j]}'
        query_parameters = urlencode({"q": bibcode_query, 'fl': 'title,author,pubdate,date,pub,identifier,year'})
        query = "https://api.adsabs.harvard.edu/v1/search/query?{}".format(query_parameters)
        results = requests.get(query, headers=headers)

        for result in results.json()['response']['docs']:
            print(f'Processing paper: {len(papers)+1}/{len(bibcodes)}')
            data = format_paper_data(dict(result))
            papers.append(data)

    # Sort based on arxiv identifier
    return sorted(papers, key=lambda d: d[3])


def format_paper_data(result):
    '''
    Takes in the ADS OpenAPI response and extracts the information
    we want to display on the webpage.
    '''

    # Generate author list, truncate if we have too many authors
    if len(result['author']) < 25:
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
        print(f'Arxiv link not found for: {result["identifier"][0]}')
        raise KeyError

    # Shorter name for journal
    journal = {
        'arXiv e-prints': 'arxiv',
        'Monthly Notices of the Royal Astronomical Society': 'MNRAS',
        'The Astrophysical Journal': 'ApJ',
    }.get(result['pub'], '')
    if journal == '':
        print('Journal not recognised:', result['pub'])
        journal = result['pub']

    # Save parsed data
    return (
        html.escape(result['title'][0]), # Escape troublesome characters
        author,
        f'https://ui.adsabs.harvard.edu/abs/{result["identifier"][0]}',
        f'https://arxiv.org/abs/{arxiv_identifier}',
        journal,
        result['year'],
    )

    # Sort based on arxiv identifier
    return sorted(analysis_papers, key=lambda d: d[3])


def generate_publication_list(skip_query=False):

    # Hard code the introduction papers as we want the full list of names
    # TODO: Update when papers are published
    intro_papers = [
        (
            'The COLIBRE project: cosmological hydrodynamical simulations of galaxy formation and evolution',
            'Joop Schaye, Evgenii Chaikin, Matthieu Schaller, Sylvia Ploeckinger, Filip Huško, Rob McGibbon, James Trayford, Alejandro Benítez-Llambay, Camila Correa, Carlos Frenk, Alexander Richings, Victor Forouhar Moreno, Yannick Bahé, Josh Borrow, Anna Durrant, Andrea Gebek, John Helly, Adrian Jenkins, Cedric Lacey, Aaron Ludlow, Folkert Nobels',
            "https://ui.adsabs.harvard.edu/abs/2025arXiv250821126S",
            "https://arxiv.org/abs/2508.21126",
            'MNRAS',
            2026,
        ),
        (
            'COLIBRE: calibrating subgrid feedback in cosmological simulations that include a cold gas phase',
            'Evgenii Chaikin, Joop Schaye, Matthieu Schaller, Sylvia Ploeckinger, Yannick Bahé, Alejandro Benítez-Llambay, Camila Correa, Victor Forouhar Moreno, Carlos Frenk, Filip Huško, Roi Kugel, Rob McGibbon, Alexander Richings, James Trayford, Josh Borrow, Rob Crain, John Helly, Cedric Lacey, Aaron Ludlow, Folkert Nobels',
            "https://ui.adsabs.harvard.edu/abs/2025arXiv250904067C/abstract",
            "https://arxiv.org/abs/2509.04067",
            'arxiv',
            2025,
        ),
    ]

    # TODO: Update when papers are published
    method_papers = [
        (
            'A thermal-kinetic subgrid model for supernova feedback in simulations of galaxy formation',
            'Evgenii Chaikin, Joop Schaye, Matthieu Schaller, Alejandro Benítez-Llambay, Folkert Nobels, Sylvia Ploeckinger',
            f'https://ui.adsabs.harvard.edu/abs/2023MNRAS.523.3709C',
            f'https://arxiv.org/abs/2211.04619',
            'MNRAS',
            2023,
        ),
        (
            'Tests of subgrid models for star formation using simulations of isolated disc galaxies',
            'Folkert Nobels, Joop Schaye, Matthieu Schaller, Sylvia Ploeckinger, Evgenii Chaikin, and Alexander Richings', 
            f'https://ui.adsabs.harvard.edu/abs/2024MNRAS.532.3299N',
            f'https://arxiv.org/abs/2309.13750',
            'MNRAS',
            2024,
        ),
        (
            'Modelling the evolution and influence of dust in cosmological simulations that include the cold phase of the interstellar medium',
            'James Trayford, Joop Schaye, Camila Correa, Sylvia Ploeckinger, Alexander Richings, Evgenii Chaikin, Matthieu Schaller, Alejandro Benítez-Llambay, Carlos Frenk, Filip Huško',
            f'https://ui.adsabs.harvard.edu/abs/2025arXiv250513056T',
            f'https://arxiv.org/abs/2505.13056',
            'MNRAS',
            2026,
        ),
        (
            'Hybrid-chimes: A model for radiative cooling and the abundances of ions and molecules in simulations of galaxy formation',
            'Sylvia Ploeckinger, Alexander Richings, Joop Schaye, James Trayford, Matthieu Schaller, Evgenii Chaikin',
            f'https://ui.adsabs.harvard.edu/abs/2025arXiv250615773P',
            f'https://arxiv.org/abs/2506.15773',
            'MNRAS',
            2025,
        ),
        (
            'A hybrid active galactic nucleus feedback model with spinning black holes, winds and jets',
            'Filip Huško, Cedric Lacey, Joop Schaye, Matthieu Schaller, Evgenii Chaikin, Sylvia Ploeckinger, Alejandro Benítez-Llambay, Alexander Richings, James Trayford',
            'https://ui.adsabs.harvard.edu/abs/2025arXiv250905179H',
            'https://arxiv.org/abs/2509.05179',
            'arxiv',
            2025,
        ),
        (
            'Non-explosive pre-supernova feedback in the COLIBRE model of galaxy formation',
            'Alejandro Benítez-Llambay, Sylvia Ploeckinger, Joop Schaye, Alexander Richings, Evgenii Chaikin, Matthieu Schaller, James Trayford, Carlos Frenk, Filip Huško, Camila Correa',
            'https://ui.adsabs.harvard.edu/abs/2025arXiv250925309B/abstract',
            'https://arxiv.org/abs/2509.25309',
            'MNRAS',
            2026,
        ),
        (
            'A subgrid model for chemical enrichment in cosmological simulations',
            'Camila Correa et al.',
            None,
            None,
            'Submitted',
            2026,
        ),
    ]

    # Identifier of the COLIBRE ADS library
    library = 'B_qtPm4pTKePLPVL4qKRSg'
    if skip_query:
        analysis_papers = intro_papers
    else:
        analysis_papers = query_ads_library(library)

    # Write basic html file, which will be formatter with make_webpage.py
    with open('src/pages/papers.html', 'w') as file:
        file.write('<h1>COLIBRE Publications</h1>\n')
        file.write('This page contains a list of publications submitted to arXiv which make use of the COLIBRE simulations. The papers are listed in chronological order based on when they were uploaded to arXiv. Please let us know if we have missed your paper!\n\n')

        for i_section, (section_header, papers) in enumerate([
                ('Reference papers', intro_papers),
                ('Papers introducing methods developed for COLIBRE', method_papers),
                ('Analysis papers', analysis_papers),
            ]):
            file.write(f'<h2 id="sec{i_section}">{section_header}</h2>\n')
            file.write('<ol>\n')

            for paper in papers:
                file.write(f'<li><p><h5>{paper[0]}</h5>\n')
                file.write(f'<i>{paper[1]}</i><br>\n')
                file.write(f'{paper[4]} ({paper[5]})')
                if paper[2] is not None:
                    file.write(f', <a href="{paper[2]}" class="active text-decoration-none">ADS</a>')
                if paper[3] is not None:
                    file.write(f', <a href="{paper[3]}" class="active text-decoration-none">arXiv</a></p></li>\n')

            file.write('</ol>\n')
        file.write('<br>\n')
        file.write('<br>\n')
        file.write('<div class="footertext">Publications are subject to their respective publisher or preprint licenses</div>')

if __name__ == '__main__':
    generate_publication_list()
