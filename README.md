# Athena Python: A Tiramisu Compiler Python Frontend For Loading Tiramisu Programs and Building and Executing Schedules

## Introduction
Athena Python is a Python frontend for the Tiramisu compiler. It allows users to build schedules for Tiramisu programs and execute them. It also allows users to generate C++ code for their Tiramisu schedules and execute it.

## Installation
To install Athena Python, you need to install the Tiramisu compiler first. Please follow the instructions [here](https://github.com/Tiramisu-Compiler/tiramisu).

Then, you can install Athena Python by cloning this repository and running the following command:
```
git clone git@github.com:skourta/athena_python.git
cd athena_python
poetry install
```

## Usage and Features
To use Athena Python, you need to activate the virtual environment created by Poetry:
```bash
poetry shell
```

### Loading a Tiramisu Program
To load a Tiramisu program, you need to create a `TiramisuProgram` object and pass the path to the Tiramisu program to its constructor:

```python
from athena.tiramisu import TiramisuProgram

tiramisu_program = TiramisuProgram("path/to/tiramisu/program.cpp")
```

### Building a Schedule
To build a schedule for a Tiramisu program, you need to create a `Schedule` object and pass the `TiramisuProgram` object to its constructor:

```python
from athena.tiramisu import Schedule

schedule = Schedule(tiramisu_program)
```

### Scheduling
Athena Python provides a set of code transformations that can be used to build schedules for Tiramisu programs. These transformations are implemented as `TiramisuAction` objects.

To add a transformation to a schedule, you need to call the `add_optimizations` method of the `Schedule` object and pass the `TiramisuAction` object to it:

```python
from athena.tiramisu import Schedule, tiramisu_actions

schedule = Schedule(tiramisu_program)

tiramisu_action = tiramisu_actions.Parallelization([("comp00",1)])

schedule.add_optimizations([tiramisu_action])
```

You can find the list of all the transformations implemented in Athena Python [here](./athena/tiramisu/tiramisu_actions/)

### Legality Checking

To check the legality of a schedule, you need to call the `is_legal` method of the `Schedule` object:

```python
from athena.tiramisu import Schedule, tiramisu_actions

schedule = Schedule(tiramisu_program)

tiramisu_action = tiramisu_actions.Parallelization([("comp00",1)])

schedule.add_optimizations([tiramisu_action])

if schedule.is_legal():
    print("The schedule is legal")
else:
    print("The schedule is illegal")
```

### Execution

To execute a schedule, you need to call the `apply_schedule` method of the `Schedule` object:

```python
from athena.tiramisu import Schedule, tiramisu_actions

schedule = Schedule(tiramisu_program)

tiramisu_action = tiramisu_actions.Parallelization([("comp00",1)])

schedule.add_optimizations([tiramisu_action])

schedule.apply_schedule()
```


## Development

### Testing
To run the tests, you need to activate the virtual environment created by Poetry:
```bash
poetry shell
```

Then, you can run the tests using the following command:

```bash
pytest
```

### Coverage
To run the tests and generate the coverage report, you need to activate the virtual environment created by Poetry:
```bash
poetry shell
```

Then, you can run the tests using the following command:

```bash
coverage run -m pytest
```

Finally, you can generate the coverage report using the following command:

```bash
coverage report
```

For HTML coverage report, you can use the following command:

```bash
coverage html --include="athena/**/*"
```

### Code Formatting
The library uses the black code formatter. To format the code, you need to activate the virtual environment created by Poetry:
```bash
poetry shell
```

Then, you can format the code using the following command:

```bash
black .
```

You can also preferably install the black formatter extension for your code editor to format the code automatically.