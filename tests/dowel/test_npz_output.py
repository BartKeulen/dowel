import csv
import tempfile

import pytest

from dowel import NpzOutput, TabularInput
from dowel.npz_output import NpzOutputWarning


class TestNpzOutput:

    def setup_method(self):
        self.log_file = tempfile.NamedTemporaryFile()
        self.npz_output = NpzOutput(self.log_file.name)
        self.tabular = TabularInput()
        self.tabular.clear()

    def teardown_method(self):
        self.log_file.close()

    def test_record(self):
        assert False
        # foo = 1
        # bar = 10
        # self.tabular.record('foo', foo)
        # self.tabular.record('bar', bar)
        # self.csv_output.record(self.tabular)
        # self.tabular.record('foo', foo * 2)
        # self.tabular.record('bar', bar * 2)
        # self.csv_output.record(self.tabular)
        # self.csv_output.dump()

        # correct = [
        #     {'foo': str(foo), 'bar': str(bar)},
        #     {'foo': str(foo * 2), 'bar': str(bar * 2)},
        # ]  # yapf: disable
        # self.assert_csv_matches(correct)

    def test_record_inconsistent(self):
        assert False
        # foo = 1
        # bar = 10
        # self.tabular.record('foo', foo)
        # self.csv_output.record(self.tabular)
        # self.tabular.record('foo', foo * 2)
        # self.tabular.record('bar', bar * 2)

        # with pytest.warns(CsvOutputWarning):
        #     self.csv_output.record(self.tabular)

        # # this should not produce a warning, because we only warn once
        # self.csv_output.record(self.tabular)

        # self.csv_output.dump()

        # correct = [
        #     {'foo': str(foo)},
        #     {'foo': str(foo * 2)},
        # ]  # yapf: disable
        # self.assert_csv_matches(correct)

    def test_empty_record(self):
        assert False
        # self.csv_output.record(self.tabular)
        # assert not self.csv_output._writer

        # foo = 1
        # bar = 10
        # self.tabular.record('foo', foo)
        # self.tabular.record('bar', bar)
        # self.csv_output.record(self.tabular)
        # assert not self.csv_output._warned_once

    def test_unacceptable_type(self):
        assert False
        # with pytest.raises(ValueError):
        #     self.csv_output.record('foo')

    def test_disable_warnings(self):
        assert False
        # foo = 1
        # bar = 10
        # self.tabular.record('foo', foo)
        # self.csv_output.record(self.tabular)
        # self.tabular.record('foo', foo * 2)
        # self.tabular.record('bar', bar * 2)

        # self.csv_output.disable_warnings()

        # # this should not produce a warning, because we disabled warnings
        # self.csv_output.record(self.tabular)

    def assert_csv_matches(self, correct):
        assert False
        # """Check the first row of a csv file and compare it to known values."""
        # with open(self.log_file.name, 'r') as file:
        #     reader = csv.DictReader(file)

        #     for correct_row in correct:
        #         row = next(reader)
        #         assert row == correct_row
