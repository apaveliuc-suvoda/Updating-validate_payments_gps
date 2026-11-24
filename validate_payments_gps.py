#!/usr/bin/env python
"""
This script will validate whether there are payments against PaymentFieldsConfigs in gps.
"""
import csv
import argparse

import django

if __name__ == '__main__':
    django.setup()

from django.db import transaction
from django.contrib.auth import get_user_model

from ecgps_core.models import PaymentFieldsConfig
from ecgps_core.models import Study
from conf.otel import init_opentelemetry

USER = get_user_model()
HEADER = ['short_name', 'payment_group']

def upload_file(filepath, parser):
    try:
        with open(filepath, 'r') as csv_file:

            # Check for empty
            start_position = csv_file.tell()
            if not csv_file.read(1):
                parser.exit('Error: Empty file')
            # Reset cursor position
            csv_file.seek(start_position)
            
            csv_reader = csv.DictReader(csv_file)

            # Sanitize the header
            csv_reader.fieldnames = [field_name.strip().lower() for field_name in csv_reader.fieldnames]

            # Check if the header is conform with the header template
            if not set(HEADER).issubset(set(csv_reader.fieldnames)):
                parser.exit(f"Error: Wrong header. Expected header: {', '.join(HEADER)}")
            
            # Filter the records
            rows = []
            for raw_record in csv_reader:
                cleaned_record = {}
                for field_name, cell_value in raw_record.items():
                    cell_value = cell_value.strip()
                    cleaned_record[field_name] = cell_value
                rows.append(cleaned_record)
                
        return rows
    
    except FileNotFoundError:
        parser.exit('Error: File not found')
    except PermissionError:
        parser.exit('Error: Permission denied')
    except UnicodeDecodeError:
        parser.exit('Error: Can not be decoded')

def main(args, parser):

    rows = upload_file(args.upload_file, parser)
    for row in rows:
        study = Study.objects.get(protocol=args.protocol)
        short_name = row['short_name']
        payment_group = row['payment_group']
        pfcs = PaymentFieldsConfig.objects.filter(study=study, short_name=short_name, payment_group_name=payment_group)

        for pfc in pfcs:
            if pfc.payment_set.exists():
                print(f'Fail : {pfc.id} : {short_name}. This Payment Schedule CANNOT be Deleted')
            else:
                print(f'Pass : {pfc.id} : {short_name}. This Payment Schedule CAN be Deleted')

if __name__ == '__main__':

    init_opentelemetry(
        resource_attrs={
            "service.name": "suvoda.site-payments",
            "service.subtype": "support",
        })

    parser = argparse.ArgumentParser(description=('description'))
    parser.add_argument(
        '--user', 
        help='Email of user running the script', 
        required=True
    )
    parser.add_argument(
        '--upload_file',
        help=f"The file path of the upload file. Expected header: {', '.join(HEADER)})",
        required=True,
    )
    parser.add_argument(
        '--ticket',
        help='The ticket number this script is associated with',
        required=True,
    )
    parser.add_argument(
        '--protocol', 
        help='Enter the protocol', 
        required=True)

    args = parser.parse_args()
    AGENT = USER.objects.get(email=args.user)
    main(args, parser)