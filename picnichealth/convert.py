#!/usr/bin/env python

"""A simple python script template.
"""

from __future__ import print_function
import os
import sys
import argparse
import csv
import shutil
import json
import io
from enum import Enum

import logging
logger = logging.getLogger(__name__)


class PicnicHealth(object):
    """ Facilitates the processing and transformation of a PicnicHealth CSV export into a PPM usable format """

    # Define PicnicHealth resource types
    class Resource(Enum):
        CareSite = 'careSite'
        Concept = 'concept'
        Condition = 'condition'
        ConditionReadable = 'conditionReadable'
        DicomStudy = 'dicomStudy'
        Drug = 'drug'
        DrugReadable = 'drugReadable'
        Location = 'location'
        Measurement = 'measurement'
        MeasurementReadable = 'measurementReadable'
        PdfFile = 'pdfFile'
        Person = 'person'
        Provider = 'provider'
        Visit = 'visit'
        Note = 'note'

        @classmethod
        def person_resources(cls):
            """ Return a list of resource types that link to Person objects directly """
            return [r for r in PicnicHealth.Resource if r not in
                    PicnicHealth.Resource.visit_resources() + PicnicHealth.Resource.care_site_resources()]

        @classmethod
        def visit_resources(cls):
            """ Return a list of resource types that link to Visit objects """
            return [PicnicHealth.Resource.CareSite, PicnicHealth.Resource.Provider]

        @classmethod
        def care_site_resources(cls):
            """ Return a list of resource types that link to Care Site objects """
            return [PicnicHealth.Resource.Location, ]

    def __init__(self, directory, output, force=False, dry=False):
        self.directory = directory
        self.output = output
        self.force = force
        self.dry = dry

    def _path_for_resource(self, resource):
        """
        Returns the path to the resource type's CSV file, considering the current working directory
        :param resource: A PicnicHealth resource type
        :type resource: PicnicHealth.Resource
        :return: The path to the CSV
        :rtype: str
        """
        return os.path.join(self.directory, '{}.csv'.format(resource.value))

    def prepare_output_path(self, path):
        """
        Accepts a path and prepares the directory for files to be written from the conversion process
        :param path: The path to check
        :return: Whether the output path is ready or not
        """
        # Check if exists
        if os.path.exists(path) and \
                input("File exists at '{}', overwrite contents (n)?".format(path)) not in ['y', 'yes']:
            return False
        elif not os.path.exists(os.path.dirname(path)):
            try:
                if not self.dry:
                    os.mkdir(os.path.dirname(path))
            except:
                raise ValueError("Could not create owner directory '{}'".format(os.path.dirname(path)))

        return True

    def get_sheet(self, resource):
        """
        Accepts a PicnicHealth resource type and attempts to read in its sheet
        :param resource: A PicnicHealth resource type
        :type resource: PicnicHealth.Resource
        :return: The sheet, if read successfully
        :rtype: csv.DictReader
        """
        try:
            # Check path
            path = self._path_for_resource(resource)
            if not os.path.exists(path):
                print(f'Error: File "{path}" for {resource.name} does not exist')
                return None

            # Dump the JSON document
            with open(path, 'r') as f:
                yield csv.DictReader(f)

        except Exception as e:
            print(f'Error: {e}')

        return None

    def extract_resources(self, resource, key=None, value=None, values=None):
        """
        Accepts a csv.DictReader and extracts the rows that match the passed key (fieldname) and value. Returns a list
        of dictionary objects parsed from the sheet's matching rows.
        :param resource: A PicnicHealth resource type whose CSV should be looked into for matching rows
        :type resource: PicnicHealth.Resource
        :param key: The key or fieldname to perform matching lookups on
        :type key: str
        :param value: The value that the passed key or fieldname should match in order to confirm a matching row/resource
        :type value: str
        :param values: The values that the passed key or fieldname should match in order to confirm a matching row/resource
        :type values: list
        :return: A list of objects
        :rtype: list
        """
        f = None
        try:
            # Check value/values
            if value is not None and values is not None:
                print('Warning: Both "value" and "values" are specified, priority is given to "value"')

            # Check path
            path = self._path_for_resource(resource)
            if not os.path.exists(path):
                print(f'Error: File "{path}" for {resource.name} does not exist')
                return None

            # Dump the JSON document
            f = open(path, 'r')
            sheet = csv.DictReader(f)

            # Collect resources
            resources = []

            # Find those related to this person
            for sheet_row in sheet:
                # Compare to value, if passed
                if key is not None:
                    if value is not None and key in sheet_row and sheet_row[key] != value:
                        continue
                    # Compare to values, if passed
                    elif values is not None and key in sheet_row and sheet_row[key] not in values:
                        continue

                # Add it to JSON
                resource = {}
                for fieldname in iter(sheet.fieldnames):
                    try:
                        # If it's a nested JSON object, parse it first
                        resource[fieldname] = json.loads(sheet_row[fieldname])
                    except json.JSONDecodeError:
                        # Else, just copy it over
                        resource[fieldname] = sheet_row[fieldname]

                # Add it
                resources.append(resource)

            # Close file
            f.close()

            return resources

        except Exception as e:
            logger.exception(f'Error: {e}', exc_info=True)
            # Clean up
            if f:
                f.close()

        return None

    def output_csv(self, resource, owner, resources):
        """
        Accepts a list of resources and exports the list of resources to a CSV file at the passed path
        :param resource: A PicnicHealth resource type whose CSV should be looked into for matching rows
        :type resource: PicnicHealth.Resource
        :param owner: The owner's ID, determines where files are saved in the output
        :type owner: str
        :param resources: A list of dictionary objects describing rows for the outgoing CSV
        :type resources: list
        :return: Whether the write performed successfully or not
        :rtype: bool
        """
        output_f = None
        try:
            # Determine output path
            path = os.path.join(self.output, owner, '{}.csv'.format(resource.value))

            # Prepare output path
            if not self.prepare_output_path(path=path):
                return False

            # Collect fieldnames
            fieldnames = []
            for resource in resources:
                fieldnames = list(set(fieldnames + list(resource.keys())))

            # Start the writer
            output_f = open(path, 'w') if not self.dry else io.StringIO()
            sheet_writer = csv.DictWriter(output_f, fieldnames=fieldnames)
            sheet_writer.writeheader()

            # Find those related to this person
            for resource in resources:

                # Write it
                sheet_writer.writerow(resource)

            # Check dry run
            if self.dry:
                print('DRY: Would have saved resources to "{}"'.format(path))

            # Close files
            output_f.close()

            return True

        except Exception as e:
            logger.exception(f'Error: {e}', exc_info=True)
            # Clean up
            if output_f:
                output_f.close()

        return False

    def split_csv(self, resource, owner, key=None, value=None, values=None):
        """
        Accepts a csv.DictReader and extracts the rows that match the passed key (fieldname) and value. Matching
        rows are copied to a new CSV at the passed path.
        :param resource: A PicnicHealth resource type whose CSV should be looked into for matching rows
        :type resource: PicnicHealth.Resource
        :param owner: The owner's ID, determines where files are saved in the output
        :type owner: str
        :param key: The key or fieldname to perform matching lookups on
        :type key: str
        :param value: The value that the passed key or fieldname should match in order to confirm a matching row/resource
        :type value: str
        :param values: The values that the passed key or fieldname should match in order to confirm a matching row/resource
        :type values: list
        :return: Whether the write performed successfully or not
        :rtype: bool
        """
        f = None
        output_f = None
        try:
            # Determine output path
            path = os.path.join(self.output, owner, '{}.csv'.format(resource.value))

            # Prepare output path
            if not self.prepare_output_path(path=path):
                return False

            # Check path
            sheet_path = self._path_for_resource(resource)
            if not os.path.exists(sheet_path):
                print(f'Error: File "{sheet_path}" for {resource.name} does not exist')
                return None

            # Dump the JSON document
            f = open(sheet_path, 'r')
            sheet = csv.DictReader(f)

            # Start the writer
            output_f = open(path, 'w') if not self.dry else io.StringIO()
            sheet_writer = csv.DictWriter(output_f, fieldnames=sheet.fieldnames)
            sheet_writer.writeheader()

            # Find those related to this person
            rows = 0
            for sheet_row in sheet:
                # Compare to value, if passed
                if key is not None:
                    if value is not None and key in sheet_row and sheet_row[key] != value:
                        continue
                    # Compare to values, if passed
                    elif values is not None and key in sheet_row and sheet_row[key] not in values:
                        continue

                # Write it
                sheet_writer.writerow(sheet_row)
                rows += 1

            # Check dry run
            if self.dry:
                print('DRY: Would have split {} rows for "{}"="{}" -> "{}"'.format(rows, key, value, path))

            # Close files
            output_f.close()

            return True

        except Exception as e:
            logger.exception(f'Error: {e}', exc_info=True)
            # Clean up
            if output_f:
                output_f.close()
            if f:
                f.close()

        return False

    def output_json(self, resource, owner, resources):
        """
        Accepts a list of resources and exports the list of resources to a JSON file at the passed path
        :param resource: A PicnicHealth resource type whose CSV should be looked into for matching rows
        :type resource: PicnicHealth.Resource
        :param owner: The owner's ID, determines where files are saved in the output
        :type owner: str
        :param resources: A list of dictionary objects describing rows for the outgoing JSON
        :type resources: list
        :return: Whether the write performed successfully or not
        :rtype: bool
        """
        f = None
        try:
            # Get the path
            path = os.path.join(self.output, owner, '{}.json'.format(resource.value))

            # Prepare output path
            if not self.prepare_output_path(path=path):
                return False

            # Get the file handle to write to
            f = open(path, 'w') if not self.dry else io.StringIO()

            # Dump the JSON document
            json.dump(resources, f)

            # Check dryrun
            if self.dry:
                print('DRY: Would have written resources to "{}"'.format(path))

            # Close it
            f.close()

            return True

        except Exception as e:
            logger.exception(f'Error: {e}', exc_info=True)
            # Clean up
            if f:
                f.close()

        return False

    def csv(self):
        """
        Runs the conversion operation on the input directory's CSV sheets. Outputs only CSV
        each person in their own directory within the specified output directory
        """
        # Get Persons
        persons = self.extract_resources(resource=PicnicHealth.Resource.Person)
        for person in persons:

            # Get their ID create a placeholder for visits
            person_id = person['personId']
            provider_ids = None
            care_site_ids = None

            # Extract resources
            for resource in PicnicHealth.Resource.person_resources():

                # Split
                self.split_csv(resource=resource, owner=person_id, key='personId', value=person_id)

                # If visits, pull linked resource IDs
                if resource is PicnicHealth.Resource.Visit:

                    # Get resources and extract provider and care site IDs
                    resources = self.extract_resources(resource=resource, key='personId', value=person_id)
                    provider_ids = list(set([r.get('performingProviderId') for r in resources if
                                             r.get('performingProviderId')] +
                                            [r.get('referringProviderId') for r in resources if
                                             r.get('referringProviderId')]))
                    care_site_ids = list(set([r.get('careSiteId') for r in resources if r.get('careSiteId')]))

            # Get location IDs now since we needed care sites to be processed
            resources = self.extract_resources(resource=PicnicHealth.Resource.CareSite,
                                               key='careSiteId', values=care_site_ids)
            location_ids = list(set([r.get('locationId') for r in resources if r.get('locationId')]))

            # Split the rest
            self.split_csv(resource=PicnicHealth.Resource.Provider, owner=person_id,
                           key='providerId', values=provider_ids)
            self.split_csv(resource=PicnicHealth.Resource.CareSite, owner=person_id,
                           key='careSiteId', values=care_site_ids)
            self.split_csv(resource=PicnicHealth.Resource.Location, owner=person_id,
                           key='locationId', values=location_ids)

    def json(self):
        """
        Runs the conversion operation on the input directory's CSV sheets. Outputs JSON for
        each person in their own directory within the specified output directory
        """
        # Get Persons
        persons = self.extract_resources(resource=PicnicHealth.Resource.Person)
        for person in persons:

            # Get their ID create a placeholder for visits
            person_id = person['personId']
            provider_ids = None
            care_site_ids = None
            location_ids = None

            # Extract resources
            for resource in PicnicHealth.Resource.person_resources():

                # Extract
                resources = self.extract_resources(resource=resource, key='personId', value=person_id)
                if not resources:
                    continue

                # Export to JSON
                self.output_json(resource=resource, owner=person_id, resources=resources)

                # Save them if visits
                if resource is PicnicHealth.Resource.Visit:

                    # Get provider and care site IDs
                    provider_ids = list(set([r.get('performingProviderId') for r in resources if
                                             r.get('performingProviderId')] +
                                            [r.get('referringProviderId') for r in resources if
                                             r.get('referringProviderId')]))
                    care_site_ids = list(set([r.get('careSiteId') for r in resources if r.get('careSiteId')]))

                elif resource is PicnicHealth.Resource.CareSite:

                    # Get location IDs
                    location_ids = list(set([r.get('locationId') for r in resources if r.get('locationId')]))

            # Process providers
            providers = self.extract_resources(resource=PicnicHealth.Resource.Provider,
                                                       key='providerId', values=provider_ids)

            # Export to JSON
            self.output_json(resource=PicnicHealth.Resource.Provider, owner=person_id, resources=providers)

            # Process care sites
            care_sites = self.extract_resources(resource=PicnicHealth.Resource.CareSite,
                                                        key='careSiteId', values=care_site_ids)

            # Export to JSON
            self.output_json(resource=PicnicHealth.Resource.CareSite, owner=person_id, resources=care_sites)

            # Process locations
            locations = self.extract_resources(resource=PicnicHealth.Resource.Location,
                                                       key='locationId', values=location_ids)

            # Export to JSON
            self.output_json(resource=PicnicHealth.Resource.Location, owner=person_id, resources=locations)


def main(arguments):

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('operations', help="The operations to run on the input CSV sheets", nargs='+',
                        type=str, choices=['csv', 'json'])
    parser.add_argument('-i', '--input', help="Path to directory containing the export CSV sheets",
                        type=str, default=os.path.abspath('.'))
    parser.add_argument('-o', '--output', help="Path to directory where outputs should be created",
                        type=str, default=os.path.abspath('.'))
    parser.add_argument('-f', '--force', help="Automatically overwrite existing files without asking first",
                        action='store_true')
    parser.add_argument('-n', '--dryrun', help="Perform a dry-run and do not write any output files",
                        action='store_true')
    args = parser.parse_args(arguments)

    # Ensure they exist
    if not os.path.exists(args.input):
        raise ValueError('Input directory "{}" does not exist'.format(args.input))

    if not os.path.exists(args.output):
        try:
            if args.dryrun:
                os.mkdir(args.output)
        except:
            raise ValueError('Error: Could not create output directory "{}"'.format(args.output))

    # Create the object
    picnichealth = PicnicHealth(directory=args.input, output=args.output, force=args.force, dry=args.dryrun)

    # Run the operation for each output
    for operation in args.operations:
        getattr(picnichealth, operation)()


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
