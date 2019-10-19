"""Tests for the TessTransitLightcurveLabelPerTimeStepDatabase class."""
from pathlib import Path

import pytest
import numpy as np
import pandas as pd

from photometric_database.tess_transit_lightcurve_label_per_time_step_database import \
    TessTransitLightcurveLabelPerTimeStepDatabase


class TestTessTransitLightcurveLabelPerTimeStepDatabase:
    """Tests for the TessTransitLightcurveLabelPerTimeStepDatabase class."""

    @pytest.fixture
    def data_directory_path(self) -> str:
        """
        Provides a path to a data directory.

        :return: The data directory path.
        """
        return 'photometric_database/tests/resources/test_data_directory/tess'

    @pytest.fixture
    def database(self, data_directory_path) -> TessTransitLightcurveLabelPerTimeStepDatabase:
        """
        Sets up the database for use in a test.

        :return: The database.
        """
        return TessTransitLightcurveLabelPerTimeStepDatabase(data_directory_path)

    def test_can_collect_lightcurve_paths(self, database):
        lightcurve_paths = database.collect_lightcurve_file_paths()
        assert len(lightcurve_paths) == 5
        assert any(path.name == 'tess2018206045859-s0001-0000000117544915-0120-s_lc.fits' for path in lightcurve_paths)

    def test_can_collect_data_validations_by_tic_id(self, database):
        data_validation_dictionary = database.collect_data_validation_dictionary()
        assert len(data_validation_dictionary) == 3
        assert any(path.name == 'tess2018206190142-s0001-s0001-0000000117544915-00106_dvr.xml'
                   for path in data_validation_dictionary.values())

