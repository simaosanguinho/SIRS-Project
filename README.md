# A17 MotorIST Read Me

## Team

| Number | Name              | User                             | E-mail                              |
| -------|-------------------|----------------------------------| ------------------------------------|
| 99309  | Rafael Girão     | https://github.com/simaosanguinho   | <mailto:rafael.s.girao@tecnico.ulisboa.pt>   |
| 102082  | Simão Sanguinho      | https://github.com/rafaelsgirao    | <mailto:simaosanguinho@tecnico.ulisboa.pt>     |
| 103252  | José Pereira  | https://github.com/pereira0x | <mailto:jose.a.pereira@tecnico.ulisboa.pt> |


![Rafael](img/ist199309.png) ![Simão](img/ist1102082.png) ![José](img/ist1103252.png)


## Contents

This repository contains documentation and source code for the *Network and Computer Security (SIRS)* project.

The [REPORT](REPORT.md) document provides a detailed overview of the key technical decisions and various components of the implemented project.
It offers insights into the rationale behind these choices, the project's architecture, and the impact of these decisions on the overall functionality and performance of the system.

This document presents installation and demonstration instructions.

*(adapt all of the following to your project, changing to the specific Linux distributions, programming languages, libraries, etc)*

## Installation

To see the project in action, it is necessary to setup a virtual environment, with N networks and M machines.  

The following diagram shows the networks and machines:

*(include a text-based or an image-based diagram)*

### Prerequisites

All the virtual machines are based on: Linux 64-bit, Kali 2023.3  

[Download](https://...link_to_download_installation_media) and [install](https://...link_to_installation_instructions) a virtual machine of Kali Linux 2023.3.  
Clone the base machine to create the other machines.

*(above, replace witch actual links)*

### Machine configurations

For each machine, there is an initialization script with the machine name, with prefix `init-` and suffix `.sh`, that installs all the necessary packages and makes all required configurations in the a clean machine.

Inside each machine, use Git to obtain a copy of all the scripts and code.

```sh
$ git clone https://github.com/tecnico-sec/cxx...
```

*(above, replace with link to actual repository)*

Next we have custom instructions for each machine.

#### Machine 1

This machine runs ...

*(describe what kind of software runs on this machine, e.g. a database server (PostgreSQL 16.1))*

To verify:

```sh
$ setup command
```

*(replace with actual commands)*

To test:

```sh
$ test command
```

*(replace with actual commands)*

The expected results are ...

*(explain what is supposed to happen if all goes well)*

If you receive the following message ... then ...

*(explain how to fix some known problem)*

#### Machine ...

*(similar content structure as Machine 1)*

## Demonstration

Now that all the networks and machines are up and running, ...

*(give a tour of the best features of the application; add screenshots when relevant)*

```sh
$ demo command
```

*(replace with actual commands)*

*(IMPORTANT: show evidence of the security mechanisms in action; show message payloads, print relevant messages, perform simulated attacks to show the defenses in action, etc.)*

This concludes the demonstration.

## Additional Information

### Links to Used Tools and Libraries

- [Java 11.0.16.1](https://openjdk.java.net/)
- [Maven 3.9.5](https://maven.apache.org/)
- ...

### Versioning

We use [SemVer](http://semver.org/) for versioning.  

### License

This project is licensed under the MIT License - see the [LICENSE.txt](LICENSE.txt) for details.

*(switch to another license, or no license, as you see fit)*

----
END OF README






# SIRS-Project

Network and Systems Security

Project Guidelines:

- [Project Overview](https://github.com/tecnico-sec/Project-2025_1/blob/main/project_overview.md)
- [Project Scenarios](https://github.com/tecnico-sec/Project-2025_1/blob/main/project_scenarios.md)

The chosen scenario was MotorIST.

## Crypto Lib

#### How to test the crypto lib:

There is a script that was develop to aid in such task. It can be found at [test](./test) directory.

To run the script, run the command:

```bash
./cryptolib_test.sh  <COMMAND>
```

The available commads are:

- `run_protect` - to run the protect functionality of cryptolab, that takes a json file and ecrypts a set of given fields;

# References

- https://smallstep.com/blog/everything-pki/
- https://security.stackexchange.com/questions/74345/provide-subjectaltname-to-openssl-directly-on-the-command-line
- https://github.com/tecnico-sec/Java-Crypto-Details
- https://kubernetes.io/docs/tasks/administer-cluster/certificates/
- https://www.yubico.com/resources/glossary/what-is-certificate-based-authentication/
