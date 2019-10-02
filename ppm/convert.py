#!/usr/bin/env python

"""A simple python script template.
"""

from __future__ import print_function
import os
import sys
import argparse
import json
import io
from unittest import mock

from ppmutils.fhir import FHIR
from ppmutils.ppm import PPM

import logging
logger = logging.getLogger(__name__)


class PPMFHIR(object):
    """ Facilitates the processing and transformation of a PPM FHIR export into a simplified PPM usable format """

    def __init__(self, fhir, ppm_id, output, force=False, dry=False):
        self.fhir = fhir
        self.ppm_id = ppm_id
        self.output = output
        self.force = force
        self.dry = dry

    def prepare_output_path(self, path):
        """
        Accepts a path and prepares the directory for files to be written from the conversion process
        :param path: The path to check
        :return: Whether the output path is ready or not
        """
        # Check if exists
        if os.path.exists(path) and not self.force and \
                input("File exists at '{}', overwrite contents (n)?".format(path)) not in ['y', 'yes']:
            return False
        elif not os.path.exists(os.path.dirname(path)):
            try:
                if not self.dry:
                    os.mkdir(os.path.dirname(path))
            except:
                raise ValueError("Could not create owner directory '{}'".format(os.path.dirname(path)))

        return True

    @mock.patch.object(PPM, 'fhir_url')
    def convert(self, fhir_url_mock):
        """
        Runs the conversion operation and saves the output JSON to the specified location
        :return: Whether the write performed successfully or not
        :rtype: bool
        """
        # Patch how FHIR gets the FHIR method it sends requests to
        def side_effect():
            return self.fhir
        fhir_url_mock.side_effect = side_effect

        f = None
        try:
            # Get the output path
            path = os.path.join(self.output, '{}.ppmdata.json'.format(self.ppm_id))

            # Prepare output path
            if not self.prepare_output_path(path=path):
                return False

            # Get the file handle to write to
            f = open(path, 'w') if not self.dry else io.StringIO()

            # Build the document
            data = FHIR.get_participant(patient=self.ppm_id, flatten_return=True)

            # Remove consent
            data.pop('composition')

            # Remove test-study stuff
            data.pop('neer')

            # Check dryrun
            if self.dry:
                print('DRY: Would have written resources to "{}"'.format(path))
            else:
                json.dump(data, f)

            # Close it
            f.close()

            return True

        except Exception as e:
            logger.exception(f'Error: {e}', exc_info=True)
            # Clean up
            if f:
                f.close()

        return False


def main(arguments):

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('fhir', help="The URL of the FHIR instance to query", type=str)
    parser.add_argument('participant', help="The ID of the participant whose data we are pulling", type=str)
    parser.add_argument('-o', '--output', help="Path to directory where output should be created",
                        type=str, default=os.path.abspath('.'))
    parser.add_argument('-f', '--force', help="Automatically overwrite existing files without asking first",
                        action='store_true')
    parser.add_argument('-n', '--dryrun', help="Perform a dry-run and do not write any output files",
                        action='store_true')
    args = parser.parse_args(arguments)

    # Ensure they exist
    if not os.path.exists(args.output):
        try:
            if args.dryrun:
                os.mkdir(args.output)
        except:
            raise ValueError('Error: Could not create output directory "{}"'.format(args.output))

    # Create the object
    ppmfhir = PPMFHIR(fhir=args.fhir, ppm_id=args.participant, output=args.output, force=args.force, dry=args.dryrun)

    # Run the operation
    ppmfhir.convert()


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
