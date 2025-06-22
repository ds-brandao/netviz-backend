import asyncio
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

session = requests.Session()
session.verify = False
session.auth = ('admin', 'xuwzuc-rExzo3-hotjed')

try:
    # Check what indexes exist
    response = session.get('https://192.168.0.132:9200/_cat/indices?v&s=index')
    print('Available indexes:')
    print(response.text)
    
    # Test aggregation to see log counts per index
    agg_query = {
        'size': 0,
        'query': {
            'bool': {
                'must': [
                    {
                        'range': {
                            '@timestamp': {
                                'gte': 'now-1h'
                            }
                        }
                    }
                ]
            }
        },
        'aggs': {
            'by_index': {
                'terms': {
                    'field': '_index',
                    'size': 20
                }
            }
        }
    }
    
    response = session.post('https://192.168.0.132:9200/*-logs/_search', json=agg_query)
    print('\nAggregation response status:', response.status_code)
    if response.status_code == 200:
        data = response.json()
        print('Recent logs (last 1 hour) by index:')
        if 'aggregations' in data and 'by_index' in data['aggregations']:
            for bucket in data['aggregations']['by_index']['buckets']:
                print(f"  - {bucket['key']}: {bucket['doc_count']} logs")
        else:
            print('  No recent logs found')
    else:
        print('Error:', response.text)
    
    # Test with longer time range
    print('\n' + '='*50)
    print('Testing with 6 hour range...')
    
    query = {
        'size': 20,
        'sort': [{'@timestamp': {'order': 'desc'}}],
        'query': {
            'bool': {
                'must': [
                    {
                        'range': {
                            '@timestamp': {
                                'gte': 'now-6h'
                            }
                        }
                    }
                ]
            }
        }
    }
    
    response = session.post('https://192.168.0.132:9200/*-logs/_search', json=query)
    if response.status_code == 200:
        data = response.json()
        print('Total hits:', data.get('hits', {}).get('total', {}).get('value', 0))
        print('Sample logs from different indexes:')
        indexes_seen = set()
        for hit in data.get('hits', {}).get('hits', []):
            index = hit.get('_index', 'unknown')
            if index not in indexes_seen:
                indexes_seen.add(index)
                log_msg = hit.get('_source', {}).get('log', 'no log field')[:100]
                timestamp = hit.get('_source', {}).get('@timestamp', 'no timestamp')
                print(f"  - {index} ({timestamp}): {log_msg}")
            if len(indexes_seen) >= 5:
                break
        
except Exception as e:
    print('Error:', e)