#!/usr/bin/env python
"""
This script will validate whether there are payments against PaymentFieldsConfigs in gps.
"""
import django

if __name__ == "__main__":
    django.setup()

from django.db import transaction

from ecgps_core.models import User
from helpers.exceptions import DryRunException
from gpmodels.utils import AgencyContext
from ecgps_core.models import PaymentFieldsConfig
from ecgps_core.models import Study, Payment
import csv


def input_file(filepath):
    rows = []
    with open(filepath, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        headers = reader.fieldnames
        for row in reader:
            rows.append(row)
    return rows, headers


def main(args):

    rows, headers = input_file(args.filepath)
    for row in rows:
        study = Study.objects.get(protocol=args.protocol)
        short_name = row["short_name"]
        pfc = PaymentFieldsConfig.objects.get(
            study=study, short_name=short_name, payment_group_name=row["payment_group"]
        )

        if pfc.payment_set.exists():
            print(
                f"Fail : {pfc.id} : {short_name}. This Payment Schedule CANNOT be Deleted"
            )

        else:
            print(
                f"Pass : {pfc.id} : {short_name}. This Payment Schedule CAN be Deleted"
            )


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(description=("description"))
    parser.add_argument("--user", help="enter your email address", required=True)
    parser.add_argument(
        "--ticket",
        help="the JIRA ticket this script is associated with and a brief "
        "description of the action you are taking with no specific data",
        required=True,
    )
    parser.add_argument("--protocol", help="Enter the protocol", required=True)
    parser.add_argument(
        "--filepath",
        help="Filepath (headers: short_name, payment_group) ",
        required=True,
    )
    args = parser.parse_args()
    AGENT = User.objects.get(email=args.user)
    main(args)