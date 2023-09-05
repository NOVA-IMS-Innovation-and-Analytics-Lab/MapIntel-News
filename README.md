# MapIntel News

A collection of instructions and corresponding scripts to prepare data and models of the MapIntel instance called **MapIntel
News**.

## Python virtual environment

Initially create a Python virtual environment and install the dependencies:

```
pip install -r requirements.txt
```

## CLI

### Configuration

Before running any of the following commands you need to configure the AWS profile name and make sure that you have permission to
interact and deploy the various services.

### Usage

The command `python cli.py` will be used to set up the MapIntel instance. You can get help for any of the commands using the
`--help` flag. The CLI allows to show, delete, create and write functionalities on the database and models. The instance is created when the
OpenSearch database and models are deployed to OpenSearch and SageMaker respectively.

### Set up

MapIntel News is set up when the following commands are used in the order given below.

Create the database:

```
python cli.py database create
```

Populate the database:

```
python cli.py database write
```

Create the models:

```
python cli.py models models
```

Populate the database with models' predictions:

```
python cli.py models write
```

### Commands

You can also use the following commands:

Show the status of the database:

```
python cli.py database show
```

Delete the database:

```
python cli.py database delete
```

Show the status of the mdoels:

```
python cli.py models show
```

Delete the models:

```
python cli.py models delete
```
