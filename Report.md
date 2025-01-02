# A17 - MotorIST Project Report

## 1. Introduction

The MotorIST project is a project that aims to provide a secure and efficient way to manage remote car configurations, such as close/open the car, configure the AC and check the battery level. This is done by a user application installed on the user's computer or smartphone. Additionally, the car also allows for firmware updates from its manufacturer and permits maintenance tasks from the mechanic.

### 1.1. Protection Goals

Due to all the communication with the car being sensitive, the MotorIST project must be secure. The base protection goals of this project are:

- \[SR1: Confidentiality\] The car configurations can only be seen by the car owner.
- \[SR2: Integrity 1\] The car can only accept configurations sent by the car owner.
- \[SR3: Integrity 2\] The car firmware updates can only be sent by the car manufacturer.
- \[SR4: Authentication\] The car manufacturer cannot deny having sent firmware updates.

### 1.2. Security Challenge

The security challenge of this project is to ensure the following:

- \[SRB1: data privacy\] The mechanic cannot see the user configurations, even when he has the car key.
- \[SRB2: authorization\] The mechanic (when authenticated) can change any parameter of the car, for testing purposes.
- \[SRB3: data authenticity\] The user can verify that the mechanic performed all the tests to the car.

For this, it is also necessary to implement a maintenance mode on the car, which is set by the user. In this mode the car is set to the default configuration and permits maintenance tasks from a mechanic.

### 1.3. Secure Documents

The communication with the car is done using a JSON document which will have the configurations to be set on the car. Since this document is sensitive, it must be protected to ensure the confidentiality, integrity and authenticity of the data. For this, we will be using the custom library that we implemented, `cryptolib`, which will be explained in the next sections.

## 2. Project Development

### 2.1 Assumptions

Due to the nature of the project, we had to make some assumptions to simplify the implementation of the project. These assumptions are:

- The system only has one car, one mechanic, one manufacturer and two users (one that is the owner of the unique car and another that is not a car owner).
- The car key corresponds to the key of the car owner.
- The car battery always starts at 100%, and the battery level is reduced by 5% for each 10 configurations sent to the car.
- The car has a default configuration that is set when the maintenance mode is activated.
- The private key of the Certificate Authority (CA) is safe and trustworthy.

### 2.2. Secure Documents Library

#### 2.2.1. Design

MotorIST's custom cryptographic library is designed to protect, verify, and unprotect documents. Document protection ensures confidentiality, integrity, and authenticity. The following structure was created to achieve these goals.

##### 2.2.1.1. Confidentiality

To ensure that sensitive information is kept private and only accessible to authorized individuals or systems - in other words, to ensure confidentiality - the document is encrypted using the ChaCha20Poly1305 algorithm. This algorithm is an authenticated encryption with associated data (AEAD) algorithm, meaning that it provides both data confidentiality and data authenticity.

When we were thinking of which algorithm to use, we were first thinking of using AES, but we decided to use ChaCha20Poly1305 because it is optimized for software performance, making it faster than AES without hardware support. It also a [great choice](https://ieeexplore.ieee.org/document/7927078) on IoT devices, and embedded systems, which is the case of the car.

The ChaCha20-Poly1305 algorithm takes as input a 256-bit key and a 96-bit nonce to encrypt a plaintext. It is important to note that, to ensure true randomness, the nonce must be generated using a cryptographically secure random number generator. For this, we used the `token_bytes` method from the `secrets` module from Python, as it is the [documentation's recommendation](https://docs.python.org/3/library/secrets.html) for generating cryptographically secure random numbers. This random nonce will be essential as it allows that different encryptions with the same data and the same key, results in different ciphertext values.

##### 2.2.1.2. Integrity

The integrity in our system is mainly ensured by the Certificate Authority (CA), that represents the manufacturer and that will distribute to each server and client a private key as well as their own certificate. This certificate apart from being signed by the CA, it gives out the email address of the entity that it belongs to and in case the entity is an user that owns a car, it states which car they own, through the car id value. If the car wants to check that an incoming firmware update was in fact issued by the manufacturer, a certificate is sent alongside it and the car proceeds to see if the certificate is valid and through the signatures in them. When a client wants to request an alteration in a car configuration, apart from sending their certificate that is used by the car to validate their entity and ownership, it also needs to send the car key, a symmetric key that belongs to the car owner (user) and that is exchanged to the car through a mutual tls channel once the first request is made, as the car returns the error `503`. If, for any reason, the car losses its key, when the owner performs a request, they are alerted to that and obliged to send it again (and not) Once the car has its key, and the owner properly sends their certificate, the system can guarantee that only the owner can perform updates to the configuration, thus ensuring the system's integrity.

##### 2.2.1.3. Authenticity

To ensure authenticity and non-repudiation, which means that the person who appears to have performed an action is indeed the one who did it, we use asymmetric cryptography. For example, in the case of the car manufacturer, the firmware is signed using the manufacturer's private key. This signature is then verified by the car using the manufacturer's public key, which is distributed beforehand via the manufacturer's certificate, which prevents other entities from impersonating the manufacturer and sending malicious firmware updates.

Another way which means that if a single byte is altered, the decryption will certainly fail. Furthermore, a random nonce field is added for each of the encrypted fields in the car document, ensuring data freshness, which will prevent replay attacks, that can happen if an attacker intercepts and tries retransmits a valid data exchange to trick the system into accepting it as legitimate.

#### 2.2.2. Document Structure

An unprotected document is a JSON object with the following structure:

```json
{
  "carId": 1,
  "user": "user1",
  "configuration": {
    "ac": true,
    "driver_door": "closed",
    "tire_pressure": {
      "1": "1psi",
      "2": "3psi",
      "3": "7psi",
      "4": "1000psi"
    }
  }
}
```

Once the document is protected, it is transformed into a JSON object with the following structure:

```json
{
  "carId": 1,
  "user": "user1",
  "configuration": {
    "nonce": "rh8vYjTDPfqVnpbU",
    "ciphertext": "Zms6TnhM0FB+e7Ci+K3UNmz2N04sN4nx9Wto7vRRV9n5kIlMHPb8S9EVXYVnEEHbWvq5DVIjFFkjtPj+1eK3DBIlp8nVbK4ukL99Ikq1qV3zBHOS3QwEF3GZj1M2mFJvIGV99qYn+91VRS4IlNFCmx8rFiSy0HNxbpuyGsPD1mNkN9Vj9DSh1NgdggY5wvUJlaM="
  }
}
```

#### 2.2.3. Implementation

We implemented the `cryptolib` library in Python as the project's main programming language is Python. By using this programming language, we can easily integrate the library with the rest of the project.

To help the implementation of the cryptographic operations, we used some external cryptographic libraries, such as `cryptography`, `hashlib`, `base64` and `secrets`.

To ensure that the library is robust and easier to extend, we implemented the library using type annotation, which is a feature of Python 3.5 and later versions. This feature allows us to specify the type of the parameters and the return of the functions, making the code more readable and easier to understand.

Another feature of python that made us choose this language was the easy manipulation of raw bytes, which is necessary for the cryptographic operations.

Testing the library was done using the shell and python scripts. The tests were done to ensure that the library was working as expected and that the cryptographic operations were being done correctly. These can be found in the `tests` folder, and an explanation on how to run them can be found in the [`README.md`](./test/README.md) file.

The main functions of the library are:

- `protect`: This function takes a JSON document, a, the target fields and an output path as input and writes the protected document to the output path.
- `unprotect`: This function takes a protected document, a key, the target fields and an output path as input and writes the unprotected document to the output path.
- `check`: This function takes a protected document, a key and the target fields as input and returns a boolean indicating if the document is valid or not.
- `sign_data` and `verify_data`: These functions are used to sign and verify the signatures.

The `protect`, `unprotect` and `check` functions are the available to be used as a terminal command. The usage of these commands can be found in the [`README.md`](./src/cryptolib/README.md) file.

## 2.3 Infrastructure

### 2.3.1 Infrastructure Overview

NixOS was selected for its simplicity and its capability to be seamlessly configured and replicated. Using a single configuration file, we can effortlessly replicate identical environments across multiple machines, with variations limited to network settings and the specific services running on each machine.

QEMU was chosen because it is one of the most widely supported hypervisors, thanks to its direct kernel integration. For our requirements, it is perfectly adequate, as we are not utilizing any graphical interface.

### 2.3.2 Secure Channel Communications - mTLS

All server-server communications are secured with mutual TLS (mTLS) in-transit encryption. For example, on communications between app servers and database servers, both peers authenticate each other based on the certificates they present to one another. In addition, PostgreSQL database servers rely solely on client certificates for user authentication, providing a strong security authentication mechanism when compared to using passwords as is common practice.

### 2.3.3 Firewalls

All virtual machines have their own `iptables`-based firewall. All machines, by default, do not allow any inbound traffic and permit all outbound traffic.

In addition to these default rules, servers will allow inbound traffic on specific ports, according to the services they operate:
- Database servers (`manufacturer-db`, `car1-db`) will permit inbound traffic on TCP port `5432`;
- Web servers (`car1-web`, `manufacturer-web`) will permit inbound traffic on TCP port `443`;
- Finally, all machines have an SSH server running and will accept TCP traffic on port `22`. This SSH server is solely used for development purposes.

It's relevant to notice only webservers are directly exposed to the world, and database servers are only accessible via servers on their respective DMZ.

### 2.3.4 Public Key Infrastructure

Our security model relies on the concept of trusting one Certificate Authority, whose entity is the Manufacturer. This Certificate Authority (CA) acts as the ultimate source of truth: any Certificate and all its information, if emitted by this CA and verified to be valid at a given point in time, is completely trusted by every other entity in our project to be true.
The CA is ultimately responsible for binding public keys to entity identifiers. These identifiers, for servers, correspond to server's DNS names (e.g `car1-db.motorist.lan`), and for clients this is their e-mail address (e.g `messi@mechanic.motorist.lan`).
In addition to this authentication property, the CA is also responsible for providing critical authorization parameters for client certificates:
- It attests that a client has a specific role inside MotorIST: clients are either `user`s or `mechanic`s;
- It attests which `user` is the owner of a particular, at a particular point in time (that is, while its certificate is still valid).

All these properties are contained in the certificate's `Subject Alternative Name` (SAN)s properties, and can be inspected with the OpenSSL, or using the `step-cli` tool. For example:
```
step certificate inspect key_store/ronaldo@user.motorist.lan/entity.crt
```

In a parallel configuration to PostgreSQL authentication/authorization, all communication with the car is required to use mutual TLS, where the client's certificate is used as the sole source of both authentication and authorization truth.


## 2.4 Threat Model

One of the assumptions we made in our threat model is that the attacker has the capability to intercept network traffic and send malicious requests, but we assume that the attacker cannot compromise the actual machines.

We also assume that the keys used in the cryptographic operations are secure and were securely distributed.

If private keys are compromised, the attacker can impersonate the entity that owns the key.

If the certificate authority (CA) is compromised, the attacker can issue certificates for any entity, which can be used to impersonate that entity.

## 2.5 Protection needs and Security Challenges Response

In this section, we will explain how we addressed the specific protection needs and security challenges that were defined in the beginning of the project.

### 2.5.1. \[SR1: Confidentiality\] The car configurations can only be seen by the car owner.

To ensure that the car configurations can only be seen by the car owner, we used the `cryptolib` library to protect the documents that are sent to the car. This library encrypts the document using the ChaCha20Poly1305 algorithm, which will use the car owner's private key to encrypt the document. This way, only the car owner can decrypt the document and see the configurations.

### 2.5.2. \[SR2: Integrity 1\] The car can only accept configurations sent by the car owner.

The user in order to request for a configuration update, they need to send a certificate that is issued and properly signed by the trusted CA. With this certificate the car will be able to see if the requester is an user and that they are indeed the owner of the car, through the information that is contained inside the certificate.s

### 2.5.3. \[SR3: Integrity 2\] The car firmware updates can only be sent by the car manufacturer.

Every time the mechanic wants to update the firmware of the car, it request the manufacturer to emit a new firmware. The manufacturer creates a new firmware and send it alongside a signature that is created based on the firmware data. The mechanic receives the response and forwards it directly to the car. Once it receives the new firmware the car will validate the the signature with the firmware data, using the manufacturer public key (contained in their certificate), ensuring that the update was certainly issued by their manufacturer and only they can perform such action.

### 2.5.4. \[SR4: Authentication\] The car manufacture cannot deny having sent firmware updates.

In order to ensure that the car manufacturer cannot deny having sent firmware updates, we used the `cryptolib` library to sign the firmware that is sent to the car. This library signs the firmware using the car manufacturer's private key, which will be verified by the car using the car manufacturer's public key. This way, the car can verify that the document was indeed sent by the car manufacturer.

### 2.5.5. \[SRB1: data privacy\] The mechanic cannot see the user configurations, even when he has the car key.

In the same way we ensure that the car only accepts configuration updates that are sent by the car owner (as discussed in section 2.5.2), the car will check the certificate that is sent by the client, when the car configurations are fetched and it only gives them out if the aforesaid certificate states that the client has a role of `User`and it is the owner of the car. If the client is neither of those things (for example if they are a mechanic), the car will not deliver the car configuration, returning with error `403`.

### 2.5.6. \[SRB2: authorization\] The mechanic (when authenticated) can change any parameter of the car, for testing purposes.

Once again the car will check the certificate that is sent by the client, when the mechanic tests are sent (through the endpoint `\run-tests`) and it only accepts them if the aforesaid certificate states that the client has a role of `Mechanic`. If the client has any other role (for example if they are an user), the car will not accept the incoming tests and store them in the database, returning with error `403`.

### 2.5.7. \[SRB3: data authenticity\] The user can verify that the mechanic performed all the tests to the car.

Once the mechanic performs tests and send the results to the car, a signature is also sent and the car keeps it in the database and the current mechanic certificate in the database. When the user checks the previously performed tests, the car validates the the signature with the tests data using the mechanic public key (contained in their certificate). With that, the user is sure that it was the mechanic that performed the tests.

## 3. Conclusion

With the implementation of the MotorIST project, we were able to achieve the protection goals and security challenges that were defined in the beginning of the project. The custom cryptographic library that we implemented, `cryptolib`, was a key part of the project, as it allowed us to protect, verify and unprotect the documents that are sent to the car. This library was implemented using the Python programming language, which allowed us to easily integrate it with the rest of the project.

There are still some features and improvements that could be made to the project. For example, we could implement a web interface for the car owner to manage the car configurations, which would make it easier for the car owner to interact with the car by having a better UI/UX.

Another improvement that could be made is to implement support for multiple entities, such as multiple car owners, mechanics and car manufacturers. This would allow the project to be more flexible and to better mimic and suit a real-world scenario.

In the certificate section, we should implement a short-lived certificate, which would be more secure than the current one, as it would have a shorter validity period. This would make it harder for an attacker to use a compromised certificate to impersonate an entity. Currently, we are using a CA that is valid for 10 years, and the certificates that are issued by the CA are valid for 1 year. Another improvement that could be made is to implement a certificate revocation list (CRL), which would allow the CA to revoke certificates that are compromised or no longer needed.

In the infrastructure section, there is also room for improvement. For example, we could implement users that were not running as root, which would make the system more secure. We could also harden the server permissions, which would make it harder for an attacker to compromise the system.

This project was a great opportunity to learn more about security and cryptography, and we are very happy with the results that we achieved. The infrastructure that we implemented was also a great learning experience, as we had to deal with firewalls, certificates, CAs and other security mechanisms for the first tine.

To conclude, we are very happy with the results that we achieved in this project, and we are confident that the MotorIST project is secure and ready to be used by the users.

# References

- "Subject Alternative Name" (SAN) - https://datatracker.ietf.org/doc/html/rfc5280#section-4.2.1.6
- "Everything you should know about certificates and PKI but are too afraid to ask" - https://smallstep.com/blog/everything-pki/
- "X.509 Verification" - https://cryptography.io/en/latest/x509/verification/
- "ChaCha20Poly1305" - https://en.wikipedia.org/wiki/ChaCha20-Poly1305
- "Authenticated Encryption with Associated Data" - https://en.wikipedia.org/wiki/Authenticated_encryption
- "ChaCha20Poly1305 on IoT devices" - https://ieeexplore.ieee.org/document/7927078
