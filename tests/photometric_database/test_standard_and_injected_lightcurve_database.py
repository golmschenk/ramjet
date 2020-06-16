from unittest.mock import patch

import pytest
import numpy as np
from pathlib import Path

import ramjet.photometric_database.standard_and_injected_lightcurve_database as database_module
from ramjet.photometric_database.lightcurve_collection import LightcurveCollection
from ramjet.photometric_database.standard_and_injected_lightcurve_database import StandardAndInjectedLightcurveDatabase


class TestStandardAndInjectedLightcurveDatabase:
    @pytest.fixture
    def database(self) -> StandardAndInjectedLightcurveDatabase:
        """A fixture of the database with lightcurve collections pre-prepared"""
        database = StandardAndInjectedLightcurveDatabase()
        # Setup mock lightcurve collections.
        standard_lightcurve_collection0 = LightcurveCollection(
            lambda: [Path('standard_path0.ext')], lambda path: (np.array([10, 20, 30]), np.array([0, 1, 2])), 0)
        standard_lightcurve_collection1 = LightcurveCollection(
            lambda: [Path('standard_path1.ext')], lambda path: (np.array([20, 30, 40]), np.array([1, 2, 3])), 0)
        injectee_lightcurve_collection = LightcurveCollection(
            lambda: [Path('injectee_path.ext')], lambda path: (np.array([30, 40, 50]), np.array([2, 3, 4])), 0)
        injectable_lightcurve_collection0 = LightcurveCollection(
            lambda: [Path('injectable_path0.ext')], lambda path: (np.array([0, 10, 20]), np.array([0.5, 1, 1.5])), 0)
        injectable_lightcurve_collection1 = LightcurveCollection(
            lambda: [Path('injectable_path1.ext')], lambda path: (np.array([0, 10, 20, 30]), np.array([0, 1, 1, 0])), 0)
        database.training_standard_lightcurve_collections = [standard_lightcurve_collection0,
                                                             standard_lightcurve_collection1]
        database.training_injectee_lightcurve_collection = injectee_lightcurve_collection
        database.training_injectable_lightcurve_collections = [injectable_lightcurve_collection0,
                                                               injectable_lightcurve_collection1]
        database.validation_standard_lightcurve_collections = [standard_lightcurve_collection1]
        database.validation_injectee_lightcurve_collection = injectee_lightcurve_collection
        database.validation_injectable_lightcurve_collections = [injectable_lightcurve_collection1]
        # Setup simplified database settings
        database.batch_size = 4
        database.time_steps_per_example = 3
        database.normalize = lambda fluxes: fluxes  # Don't normalize values to keep it simple.
        return database

    def test_database_has_lightcurve_collection_properties(self):
        database = StandardAndInjectedLightcurveDatabase()
        assert hasattr(database, 'training_standard_lightcurve_collections')
        assert hasattr(database, 'training_injectee_lightcurve_collection')
        assert hasattr(database, 'training_injectable_lightcurve_collections')
        assert hasattr(database, 'validation_standard_lightcurve_collections')
        assert hasattr(database, 'validation_injectee_lightcurve_collection')
        assert hasattr(database, 'validation_injectable_lightcurve_collections')

    @pytest.mark.skip(reason='Working on unit tests that make up the parts of this functional test.')
    @pytest.mark.slow
    @pytest.mark.functional
    def test_database_can_generate_training_and_validation_datasets(self, database):
        training_dataset, validation_dataset = database.generate_datasets()
        training_batch = next(iter(training_dataset))
        assert np.array_equal(training_batch[0].numpy(), [0, 1, 2])  # Standard lightcurve 0.
        assert np.array_equal(training_batch[1].numpy(), [1, 2, 3])  # Standard lightcurve 1.
        assert np.array_equal(training_batch[2].numpy(), [1, 3, 6])  # Injected lightcurve 0.
        assert np.array_equal(training_batch[3].numpy(), [0, 3, 4])  # Injected lightcurve 1, with injectable clipped.
        validation_batch = next(iter(validation_dataset))
        assert np.array_equal(validation_batch[0].numpy(), [1, 2, 3])  # Standard lightcurve 1.
        assert np.array_equal(validation_batch[1].numpy(), [0, 3, 4])  # Injected lightcurve 1, with injectable clipped.
        assert np.array_equal(validation_batch[2].numpy(), [1, 2, 3])  # Standard lightcurve 1.
        assert np.array_equal(validation_batch[3].numpy(), [0, 3, 4])  # Injected lightcurve 1, with injectable clipped.

    def test_can_create_tensorflow_dataset_for_lightcurve_collection_paths(self, database):
        injectee_paths_dataset = database.generate_paths_dataset_from_lightcurve_collection(
            database.training_injectee_lightcurve_collection)
        assert next(iter(injectee_paths_dataset)).numpy() == b'injectee_path.ext'

    def test_lightcurve_collection_paths_dataset_is_repeated(self, database):
        with patch.object(database_module.tf.data.Dataset, 'repeat',
                          side_effect=lambda dataset: dataset, autospec=True) as mock_repeat:
            _ = database.generate_paths_dataset_from_lightcurve_collection(
                database.training_injectee_lightcurve_collection)
            assert mock_repeat.called

    def test_lightcurve_collection_paths_dataset_is_shuffled(self, database):
        with patch.object(database_module.tf.data.Dataset, 'shuffle',
                          side_effect=lambda dataset, buffer_size: dataset, autospec=True) as mock_shuffle:
            _ = database.generate_paths_dataset_from_lightcurve_collection(
                database.training_injectee_lightcurve_collection)
            assert mock_shuffle.called
            assert mock_shuffle.call_args[0][1] == database.shuffle_buffer_size

    def test_can_create_tensorflow_datasets_for_multiple_lightcurve_collections_paths(self, database):
        standard_paths_datasets = database.generate_paths_datasets_from_lightcurve_collection_list(
            database.training_standard_lightcurve_collections)
        assert next(iter(standard_paths_datasets[0])).numpy() == b'standard_path0.ext'
        assert next(iter(standard_paths_datasets[1])).numpy() == b'standard_path1.ext'
