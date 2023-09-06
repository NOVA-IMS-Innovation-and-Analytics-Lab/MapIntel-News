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

Before running any of the following commands you need to do the following: 

- Configure the AWS credentials and make sure that you have permission to interact and deploy the various services. 
- Install [just](https://just.systems/) command runner.
- Define the OpenSearch database password that you will use or already used with the command `export
  OPENSARCH_PASSWORD=your_password`.

### Usage

You can get help for the available commands using the command `just help`. The CLI allows describing and setting up the database
and models. The MapIntel instance is ready when the populated database and trained models are deployed to OpenSearch and SageMaker
respectively.

Install Python dependencies:

```
just install
```

Describe the status of the resources:

```
just describe
```

Set up the resources:

```
just setup
```
