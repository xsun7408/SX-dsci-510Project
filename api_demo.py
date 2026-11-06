"""A small live acquisition demo; analysis uses the separately saved sample."""

import argparse
import json

from acquire import DEFAULT_DEPARTMENTS, MetClient, fetch_object, get_departments, get_object_ids


# Make three live endpoint calls without changing the research sample.
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--department', type=int, default=DEFAULT_DEPARTMENTS[0])
    args = parser.parse_args()
    client = MetClient()
    departments = get_departments(client)
    names = {row['departmentId']: row['displayName'] for row in departments}
    if args.department not in names:
        parser.error('Unknown department ID')

    print('Department:', args.department, names[args.department])
    ids = get_object_ids(client, args.department)
    print('Candidate IDs:', len(ids))
    if not ids:
        raise ValueError('No IDs returned for this department')
    record = fetch_object(client, sorted(ids)[0])
    print('Full response fields:', len(record))

    # Print a readable subset of the actual full metadata response.
    fields = ['objectID', 'title', 'department', 'medium', 'culture', 'artistNationality', 'objectDate']
    print(json.dumps({field: record.get(field) for field in fields}, ensure_ascii=False, indent=2))
    print('This demo does not change the sampling manifest or research cache.')


if __name__ == '__main__':
    main()
