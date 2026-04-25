import os, json

files = [f for f in os.listdir('data') if f.endswith('.json')]
print('Files in data/:', files)

if os.path.exists('data/outbox.json'):
    with open('data/outbox.json') as f:
        data = json.load(f)
    print(f'outbox.json has {len(data)} records')
    locs = list(set(d.get('location','') for d in data))
    print('Locations sample:', locs[:5])

if os.path.exists('data/researched_leads.json'):
    with open('data/researched_leads.json') as f:
        data2 = json.load(f)
    print(f'researched_leads.json has {len(data2)} records')
    locs2 = list(set(d.get('location','') for d in data2))
    print('Researched locs sample:', locs2[:5])
