Test design
===========

This chapter describes in general how to add new test cases to Yardstick.

The relevant cases will probably be either to reuse an existing test case in
a new test suite combination, or to make minor modifications to existing YAML
files, or to create new YAML files, or to create completely new test cases
and also new test types.


General guide lines
-------------------

- Try to reuse what already exists as much as possible.

- Adhere to the patterns of the existing design, such as using scenarios,
runners and so on.

- Make sure any new code has enough test coverage. If the coverage is not good
enough the build system will complain.

- Additions and changes should be documented in a suitable fashion.
Remember not only pure coders/designers could be interested in getting a
deeper understanding of Yardstick.